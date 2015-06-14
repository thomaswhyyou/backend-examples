import uuid
from datetime import datetime

import rmanager
from bid import Bid
from item import Item
import constants as const


class Auction(rmanager.ManagedObject):
    """
    Represent an auction for a given item.

    Assumes an item can be re-auctioned if one or more auctions for the item
    have not resulted a winning bid in the past.

    No need to be used directly, instead user class should rely on the provided
    methods for a required action.
    """

    category = "auction"
    identifier = "id"

    def __init__(self, item_name):
        item = Item.one(item_name)

        self.id = str(uuid.uuid4())
        self.item_name = item.name
        self.reserved_price = item.reserved_price

        self.highest_bid_id = None
        self.winning_bid_id = None

        self.status = const.AUCTION_STATUS_CREATED
        self.created_at = str(datetime.now())
        self.started_at = None
        self.closed_at = None

        # By association to an auction, item is now staged.
        item.status = const.ITEM_STATUS_STAGED
        item.save()

    def __repr__(self):
        return "<Auction id:'{}'>".format(self.id)

    def save(self):
        # Always update the status automatically at "save".
        self.status = self.get_status()
        return super(Auction, self).save()

    def get_all_submitted_bids(self):

        def filter_func(bid_record):
            return bid_record.get("auction_id", None) == self.id

        return Bid.all(filter_func)

    def get_status(self):
        # Auction status can be derived implicitly based on timestamps(s)
        # and the state of winning_bid_id property.
        if self.closed_at:
            if self.winning_bid_id:
                return const.AUCTION_STATUS_CALLED_SUCCESS
            else:
                return const.AUCTION_STATUS_CALLED_FAIL

        elif self.started_at:
            return const.AUCTION_STATUS_IN_PROGRESS

        else:
            return const.AUCTION_STATUS_CREATED

    def start(self):
        # Auction already in progress or closed, should not restart.
        if self.status > const.AUCTION_STATUS_CREATED:
            return {
                "status": "error",
                "errors": [
                    "This auction cannot be started because it is either "
                    "already in progress or closed already."
                ],
            }

        # All good, go ahead and update necessary fields.
        self.started_at = str(datetime.now())
        self.save()

        return {
            "status": "success",
            "auction_id": self.id,
        }

    def end(self):
        # Auction already going or closed, should not restart.
        if self.status != const.AUCTION_STATUS_IN_PROGRESS:
            return {
                "status": "error",
                "errors": [
                    "This auction cannot be ended because it is currently "
                    "not in progress."
                ],
            }

        # Check if we have winning bid based on highest bid vs reserved price.
        item = Item.one(self.item_name)
        highest_bid = Bid.one(self.highest_bid_id)
        if highest_bid.offer_price >= self.reserved_price:
            self.winning_bid_id = highest_bid.id
            item.status = const.ITEM_STATUS_SOLD
        else:
            # Mark the item back so that it can be available for auction again.
            item.status = const.ITEM_STATUS_AVAILABLE

        self.closed_at = str(datetime.now())
        self.save()
        item.save()

        return {
            "status": "success",
            "auction_id": self.id,
        }

    def process_bid(self, submitted_price, participant_id):
        status = self.get_status()

        # Auction is not live; no bid to process.
        if status != const.AUCTION_STATUS_IN_PROGRESS:
            return {
                "status": "error",
                "errors": ["This auction is currently not in progress."],
            }

        # Some basic input validation.
        if submitted_price <= 0:
            return {
                "status": "error",
                "errors": ["Not a valid bid price for submission."],
            }

        # Submitted bid must beat current highest bid, otherwise not allowed.
        if self.highest_bid_id is not None:
            highest_bid = Bid.one(self.highest_bid_id)
            if submitted_price <= highest_bid.offer_price:
                return {
                    "status": "error",
                    "errors": [
                        "Bid must be higher than the current highest bid."
                    ],
                }

        # All good, save submitted bid and update necessary fields.
        bid = Bid(self.id, submitted_price, participant_id)
        self.highest_bid_id = bid.id

        bid.save()
        self.save()

        return {
            "status": "success",
            "bid_id": bid.id
        }

