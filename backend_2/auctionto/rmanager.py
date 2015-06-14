import inspect
import redis
import json


"""
A few getter/setter api for interacting with redis.

"first_key": unique string value to categorize top level key-value data.
             (e.g. "user", "item", etc)
"second_key": unique string value for second level key-value data, to store
              information of each record.

NOTE:
For second level, we will store as json string because it seems you can't
really create nested structures with redis. :\

"""


def get_one_record(first_key, second_key):
    r = redis.StrictRedis()
    maybe_record = r.hgetall(str(first_key)).get(str(second_key), None)
    if maybe_record:
        maybe_record = json.loads(maybe_record)

    return maybe_record


def get_all_records(first_key, filter_func=None):
    r = redis.StrictRedis()
    records = r.hgetall(first_key).values()
    records = [json.loads(record) for record in records]
    # I'm sure you can do this with redis more efficiently.
    if filter_func:
        records = filter(filter_func, records)

    return records


def set_one_record(first_key, second_key, data):
    r = redis.StrictRedis()
    return r.hmset(first_key, {second_key: json.dumps(data)})


def delete_one_record(first_key, second_key):
    r = redis.StrictRedis()
    return r.hdel(first_key, second_key)


def flushall():
    r = redis.StrictRedis()
    return r.flushall()


"""
Base managed object class for our library that uses the above functions to help
manage our objects easier.
"""


class ManagedObject(object):

    category = "placeholder"
    identifier = "placeholder"

    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    def _make_object_from_record(cls, record):
        """
        Construct and return an instance of class based on the existing data
        saved in redis.

        """

        # First create an instance of this class by figuring out what args we
        # need for __init__ method.
        args = inspect.getargspec(cls.__init__).args[1:]  # First arg "self"
        args = [record.get(x) for x in args]
        instance = cls(*args)

        # Then update the instance for all attributes based on existing data.
        for key, val in record.items():
            setattr(instance, key, val)

        return instance

    @classmethod
    def one(cls, unique_key):
        maybe_record = get_one_record(cls.category, unique_key)
        if maybe_record is None:
            return
        return cls._make_object_from_record(maybe_record)

    @classmethod
    def all(cls, filter_func=None):
        records = get_all_records(cls.category, filter_func=filter_func)
        objects = [cls._make_object_from_record(r) for r in records]
        return objects

    def save(self):
        unique_key = getattr(self, self.identifier)
        return set_one_record(self.category, unique_key, self.__dict__)

    def delete(self):
        unique_key = getattr(self, self.identifier)
        return delete_one_record(self.category, unique_key)
