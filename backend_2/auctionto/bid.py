import uuid
from datetime import datetime

import rmanager


class Bid(rmanager.ManagedObject):
    """
    Represent each accepted bid for a given auction.

    No need to be used directly, instead user class should rely on the provided
    methods for a required action.
    """

    category = "bid"
    identifier = "id"

    def __init__(self, auction_id, offer_price, participant_id):
        self.id = str(uuid.uuid4())
        self.offer_price = offer_price
        self.auction_id = auction_id
        self.participant_id = participant_id

        self.submitted_at = str(datetime.now())

    def __repr__(self):
        return "<Bid id:'{}' price:'{}'>".format(self.id, self.offer_price)
