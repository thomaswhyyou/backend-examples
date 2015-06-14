from datetime import datetime

import rmanager
import constants as const


class Item(rmanager.ManagedObject):
    """
    Represent an item for auction.

    No need to be used directly, instead user class should rely on the provided
    methods for a required action.
    """

    category = "item"
    identifier = "name"

    def __init__(self, name, reserved_price):
        self.name = name
        self.reserved_price = reserved_price

        self.status = const.ITEM_STATUS_AVAILABLE
        self.created_at = str(datetime.now())
        self.updated_at = str(datetime.now())

    def __repr__(self):
        return "<Item name:'{}'>".format(self.name)

    def save(self):
        self.updated_at = str(datetime.now())
        return super(Item, self).save()
