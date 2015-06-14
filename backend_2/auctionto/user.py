import uuid
from datetime import datetime

import rmanager
import constants as const
from auction import Auction
from item import Item
from bid import Bid


class BaseUser(rmanager.ManagedObject):
    """
    Represent a base user class for auctioneers and participants.

    """

    category = "user"
    identifier = "id"

    def __init__(self, user_type, save=False):
        if user_type not in const.USER_TYPES:
            raise Exception("Given user type not implemented.")

        self.type = user_type
        self.id = str(uuid.uuid4())
        self.created_at = str(datetime.now())

        if save:
            self.save()

    def query_latest_summary_for_item(self, item_name):
        item = Item.one(item_name)
        if item is None:
            return {
                "status": "error",
                "errors": ["Item does not exist."],
            }

        item_info = {
            "name": item.name,
            "reserved_price": item.reserved_price,
            "status_code": item.status,
            "status_name": const.ITEM_STATUS_NAMES[item.status],
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }

        auction = None
        auction_info = None
        if item.status > const.ITEM_STATUS_AVAILABLE:

            # We will exclude any past failed auctions in summary because
            # presumably that's not good for auction.
            def filter_func(auc_record):
                item_name_met = auc_record.get("item_name") == item_name
                auc_status_met = auc_record.get("status") != const.AUCTION_STATUS_CALLED_FAIL
                return item_name_met and auc_status_met

            ret = Auction.all(filter_func)
            if ret:
                auction = ret[0]
                auction_info = {
                    "id": auction.id,
                    "status_code": auction.status,
                    "status_name": const.AUCTION_STATUS_NAMES[auction.status],
                    "highest_bid_id": auction.highest_bid_id,
                    "winning_bid_id": auction.winning_bid_id,
                    "created_at": auction.created_at,
                    "started_at": auction.started_at,
                    "closed_at": auction.closed_at,
                }

        bid_id = None
        if auction and auction.winning_bid_id:
            bid_id = auction.winning_bid_id
        elif auction and auction.highest_bid_id:
            bid_id = auction.highest_bid_id

        bid_info = None
        if bid_id:
            prevailing_bid = Bid.one(bid_id)
            if prevailing_bid:
                bid_info = {
                    "id": prevailing_bid.id,
                    "offer_price": prevailing_bid.offer_price,
                    "participant_id": prevailing_bid.participant_id,
                    "submitted_at": prevailing_bid.submitted_at,
                }

        return {
            "status": "success",
            "item": item_info,
            "auction": auction_info,
            "prevailing_bid": bid_info,
        }


class Auctioneer(BaseUser):

    def __init__(self, save=False):
        super(Auctioneer, self).__init__(const.USER_TYPE_AUCTIONEER, save=save)

    def __repr__(self):
        return "<Auctioneer id:'{}'>".format(self.id)

    @classmethod
    def all(cls, filter_func=None):
        # Make sure we only return auctioneer objects, because we share the
        # same category namespace "user".
        objects = super(Auctioneer, cls).all()
        return [o for o in objects if o.type == const.USER_TYPE_AUCTIONEER]

    def query_all_items(self, status_code=None):
        items = Item.all()
        if status_code:
            items = [i for i in items if i.status == status_code]

        return items

    def query_all_auctions(self, status_code=None):
        auctions = Auction.all()
        if status_code:
            auctions = [a for a in auctions if a.status == status_code]

        return auctions

    def query_all_bids_for_auction(self, auction_id):
        auction = Auction.one(auction_id)
        if auction is None:
            return {
                "status": "error",
                "errors": ["This auction does not exist."],
            }

        return auction.get_all_submitted_bids()

    def register_item(self, item_name, reserved_price):
        if Item.one(item_name) is not None:
            return {
                "status": "error",
                "errors": ["Item already exists."],
            }

        item = Item(item_name, reserved_price)
        item.save()

        return {
            "status": "success",
            "item_name": item.name,
        }

    def create_auction(self, item_name):
        item = Item.one(item_name)
        if item is None:
            return {
                "status": "error",
                "errors": ["Item does not exist."],
            }

        def filter_func(auc_record):
            return auc_record.get("status") != const.AUCTION_STATUS_CALLED_FAIL

        if Auction.all(filter_func):
            return {
                "status": "error",
                "errors": ["Auction already exists for this item."],
            }

        auction = Auction(item_name)
        auction.save()

        return {
            "status": "success",
            "auction_id": auction.id,
        }

    def start_auction(self, auction_id):
        auction = Auction.one(auction_id)
        if auction is None:
            return {
                "status": "error",
                "errors": ["This auction does not exist."],
            }

        return auction.start()

    def register_item_and_start_auction(self, item_name, reserved_price):
        """
        Shortcut method to register an item, create an auction, and start the
        auction in one go.

        """

        ret = self.register_item(item_name, reserved_price)
        if ret["status"] != "success":
            return ret

        ret = self.create_auction(ret["item_name"])
        if ret["status"] != "success":
            return ret

        ret = self.start_auction(ret["auction_id"])

        return ret

    def call_auction(self, auction_id):
        auction = Auction.one(auction_id)
        if auction is None:
            return {
                "status": "error",
                "errors": ["This auction does not exist."],
            }

        return auction.end()

    def update_item_reserved_price(self, item_name, reserved_price):
        item = Item.one(item_name)
        if item is None:
            return {
                "status": "error",
                "errors": ["Item does not exist."],
            }

        if item.status != const.ITEM_STATUS_AVAILABLE:
            return {
                "status": "error",
                "errors": [
                    "You cannot change the reserved price of an item that is"
                    "currently staged for auction or was sold already."
                ],
            }

        item.reserved_price = reserved_price
        item.save()

        return {
            "status": "success",
            "item_name": item.name,
        }

    def unstage_item_from_auction(self, item_name):
        item = Item.one(item_name)
        if item is None:
            return {
                "status": "error",
                "errors": ["Item does not exist."],
            }

        if item.status != const.ITEM_STATUS_STAGED:
            return {
                "status": "error",
                "errors": ["Item is not staged for auction."],
            }

        def filter_func(auc_record):
            item_name_met = auc_record.get("item_name") == item_name
            auc_status_met = auc_record.get("status") == const.AUCTION_STATUS_CREATED

            return item_name_met and auc_status_met

        ret = Auction.all(filter_func)
        if ret:
            auction = ret[0]
            auction.delete()
        else:
            return {
                "status": "error",
                "errors": [
                    "Auction for this item already progressed, and cannot "
                    "unstage the item at this time."
                ],
            }

        item.status = const.ITEM_STATUS_AVAILABLE
        item.save()

        return {
            "status": "success",
            "item_name": item.name,
        }


class Participant(BaseUser):

    def __init__(self, save=False):
        super(Participant, self).__init__(const.USER_TYPE_PARTICIPANT, save=save)

    def __repr__(self):
        return "<Participant id:'{}'>".format(self.id)

    @classmethod
    def all(cls, filter_func=None):
        # Make sure we only return participant objects, because we share the
        # same category namespace "user".
        objects = super(Participant, cls).all()
        return [o for o in objects if o.type == const.USER_TYPE_PARTICIPANT]

    def query_all_live_auctions(self, involved_only=False):

        def filter_func(auc_record):
            return auc_record.get("status") == const.AUCTION_STATUS_IN_PROGRESS

        auctions = Auction.all(filter_func)

        if involved_only:
            bids = Bid.all(lambda x: x["participant_id"] == self.id)
            involved_auction_ids = set([b.auction_id for b in bids])
            auctions = [a for a in auctions if a.id in involved_auction_ids]

        return auctions

    def submit_bid_for_auction(self, auction_id, bid_price):
        auction = Auction.one(auction_id)
        if auction is None:
            return {
                "status": "error",
                "errors": ["This auction does not exist."],
            }

        return auction.process_bid(bid_price, self.id)
