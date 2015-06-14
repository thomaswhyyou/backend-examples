# User types.
USER_TYPE_AUCTIONEER = 0
USER_TYPE_PARTICIPANT = 1

USER_TYPES = [
    USER_TYPE_AUCTIONEER,
    USER_TYPE_PARTICIPANT,
]


# Item statuses.
ITEM_STATUS_AVAILABLE = 0
ITEM_STATUS_STAGED = 1
ITEM_STATUS_SOLD = 2

ITEM_STATUS_NAMES = {
    ITEM_STATUS_AVAILABLE: "Item is available for auction",
    ITEM_STATUS_STAGED: "Item is currently staged for auction",
    ITEM_STATUS_SOLD: "Item has been sold in auction",
}


# Auction statuses.
AUCTION_STATUS_CREATED = 0
AUCTION_STATUS_IN_PROGRESS = 1
AUCTION_STATUS_CALLED_SUCCESS = 2
AUCTION_STATUS_CALLED_FAIL = 3

AUCTION_STATUS_NAMES = {
    AUCTION_STATUS_CREATED: "Auction was created with an item.",
    AUCTION_STATUS_IN_PROGRESS: "Auction is currently in progress.",
    AUCTION_STATUS_CALLED_SUCCESS: "Auction has been called with a winning bid. :)",
    AUCTION_STATUS_CALLED_FAIL: "Auction has been called without a winning bid. :(",
}
