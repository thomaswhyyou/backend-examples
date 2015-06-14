from auctionto import Auctioneer, Participant, rmanager, constants as const


if __name__ == "__main__":
    rmanager.flushall()

    auctioneer_one = Auctioneer(save=True)

    participant_one = Participant(save=True)
    participant_two = Participant(save=True)

    # Test the number of users.
    assert len(Auctioneer.all()) == 1
    assert len(Participant.all()) == 2

    # Test we currently have no auctions or items, observable by all users.
    assert len(auctioneer_one.query_all_items()) == 0
    assert len(auctioneer_one.query_all_auctions()) == 0
    assert len(participant_one.query_all_live_auctions()) == 0
    assert len(participant_two.query_all_live_auctions()) == 0

    # Have auctioneer register an item.
    ret = auctioneer_one.register_item("macbook", 800)
    assert ret["status"] == "success"
    assert ret["item_name"] == "macbook"

    # Try again with the same item, should get an error.
    ret = auctioneer_one.register_item("macbook", 800)
    assert ret["status"] == "error"
    assert "Item already exists." in ret["errors"]

    # Check one registered item is visible to auctioneer.
    assert len(auctioneer_one.query_all_items()) == 1
    assert len(auctioneer_one.query_all_auctions()) == 0
    assert len(participant_one.query_all_live_auctions()) == 0
    assert len(participant_two.query_all_live_auctions()) == 0

    # Check the latest summary on this item.
    ret = auctioneer_one.query_latest_summary_for_item("macbook")

    assert ret["status"] == "success"
    assert ret["item"]["name"] == "macbook"
    assert ret["item"]["status_code"] == const.ITEM_STATUS_AVAILABLE
    assert ret["item"]["reserved_price"] == 800
    assert ret["auction"] == None
    assert ret["prevailing_bid"] == None

    # Have auctioneer create an auction for the item.
    ret = auctioneer_one.create_auction("macbook")
    assert ret["status"] == "success"

    # Check one created auction is visible to auctioneer, but not to participants.
    assert len(auctioneer_one.query_all_items()) == 1
    assert len(auctioneer_one.query_all_auctions()) == 1
    assert len(participant_one.query_all_live_auctions()) == 0
    assert len(participant_two.query_all_live_auctions()) == 0

    # Have auctioneer unstage the item from the newly created auction.
    # Because no reason but for testing.
    ret = auctioneer_one.unstage_item_from_auction("macbook")
    assert ret["status"] == "success"

    # Check the auction without any staged item has been removed, and no auction
    # is visible to auctioneer.
    assert len(auctioneer_one.query_all_items()) == 1
    assert len(auctioneer_one.query_all_auctions()) == 0
    assert len(participant_one.query_all_live_auctions()) == 0
    assert len(participant_two.query_all_live_auctions()) == 0

    # Have auctioneer register another item and start an auction on it.
    ret = auctioneer_one.register_item_and_start_auction("iphone", 400)
    assert ret["status"] == "success"

    auction_id = ret["auction_id"]

    # Check there are two items and one auction visible to auctioneer.
    # There should be one live action visible to participants, but none involved.
    assert len(auctioneer_one.query_all_items()) == 2
    assert len(auctioneer_one.query_all_auctions()) == 1
    assert len(participant_one.query_all_live_auctions()) == 1
    assert len(participant_one.query_all_live_auctions(involved_only=True)) == 0
    assert len(participant_two.query_all_live_auctions()) == 1
    assert len(participant_two.query_all_live_auctions(involved_only=True)) == 0

    # Have participant_one submit a bid, with an invalid offer price.
    ret = participant_one.submit_bid_for_auction(auction_id, 0)
    assert ret["status"] == "error"
    assert "Not a valid bid price for submission." in ret["errors"]

    ret = participant_one.submit_bid_for_auction(auction_id, -100)
    assert ret["status"] == "error"
    assert "Not a valid bid price for submission." in ret["errors"]

    # Have participant_one submit a bid, with a valid price this time.
    ret = participant_one.submit_bid_for_auction(auction_id, 100)
    assert ret["status"] == "success"

    first_bid_id = ret["bid_id"]

    # Check participants involved live auctions.
    assert len(participant_one.query_all_live_auctions(involved_only=True)) == 1
    assert len(participant_two.query_all_live_auctions(involved_only=True)) == 0

    # Check item summary again, should have auction and bid info.
    ret = participant_one.query_latest_summary_for_item("iphone")
    assert ret["status"] == "success"
    assert ret["item"]["name"] == "iphone"
    assert ret["item"]["status_code"] == const.ITEM_STATUS_STAGED
    assert ret["item"]["reserved_price"] == 400
    assert ret["auction"]["id"] == auction_id
    assert ret["auction"]["highest_bid_id"] == first_bid_id
    assert ret["auction"]["winning_bid_id"] == None
    assert ret["auction"]["closed_at"] == None
    assert ret["prevailing_bid"]["id"] == first_bid_id
    assert ret["prevailing_bid"]["offer_price"] == 100
    assert ret["prevailing_bid"]["participant_id"] == participant_one.id

    # Have participant_two submit a higher bid, but less than reserved price.
    ret = participant_two.submit_bid_for_auction(auction_id, 200)
    assert ret["status"] == "success"

    second_bid_id = ret["bid_id"]

    # Check now both participants are involved in one live auction.
    assert len(participant_one.query_all_live_auctions(involved_only=True)) == 1
    assert len(participant_two.query_all_live_auctions(involved_only=True)) == 1

    # Check item summary again, should have updated info.
    ret = participant_one.query_latest_summary_for_item("iphone")
    assert ret["status"] == "success"
    assert ret["item"]["name"] == "iphone"
    assert ret["auction"]["highest_bid_id"] == second_bid_id
    assert ret["auction"]["winning_bid_id"] == None
    assert ret["auction"]["closed_at"] == None
    assert ret["prevailing_bid"]["id"] == second_bid_id
    assert ret["prevailing_bid"]["offer_price"] == 200
    assert ret["prevailing_bid"]["participant_id"] == participant_two.id

    # Have participant_one submit another bid, but lower than the current
    # highest bid, which should be rejected.
    ret = participant_one.submit_bid_for_auction(auction_id, 150)
    assert ret["status"] == "error"
    assert "Bid must be higher than the current highest bid." in ret["errors"]

    # Confirm currently accepted bid for this auction, should be only two.
    assert len(auctioneer_one.query_all_bids_for_auction(auction_id)) == 2

    # Have auctioneer call the auction, while reserved price is not met.
    ret = auctioneer_one.call_auction(auction_id)
    assert ret["status"] == "success"

    # Check item summary again, which should be available for auction again.
    ret = auctioneer_one.query_latest_summary_for_item("iphone")
    assert ret["item"]["name"] == "iphone"
    assert ret["item"]["status_code"] == const.ITEM_STATUS_AVAILABLE
    assert ret["item"]["reserved_price"] == 400
    assert ret["auction"] == None
    assert ret["prevailing_bid"] == None

    # Check no visible auction to both participants anymore.
    assert len(participant_one.query_all_live_auctions()) == 0
    assert len(participant_one.query_all_live_auctions(involved_only=True)) == 0
    assert len(participant_two.query_all_live_auctions()) == 0
    assert len(participant_two.query_all_live_auctions(involved_only=True)) == 0

    # Have auctioneer lower the reserved price on this item.
    ret = auctioneer_one.update_item_reserved_price("iphone", 200)
    assert ret["status"] == "success"

    # Check item summary.. yet again.
    ret = auctioneer_one.query_latest_summary_for_item("iphone")
    assert ret["item"]["name"] == "iphone"
    assert ret["item"]["status_code"] == const.ITEM_STATUS_AVAILABLE
    assert ret["item"]["reserved_price"] == 200  # Updated to be lower
    assert ret["auction"] == None
    assert ret["prevailing_bid"] == None

    # Let's start an auction on this item again.
    ret = auctioneer_one.create_auction("iphone")
    auction_id = ret["auction_id"]
    ret = auctioneer_one.start_auction(auction_id)
    assert len(participant_one.query_all_live_auctions()) == 1
    assert len(participant_two.query_all_live_auctions()) == 1

    # Have participant_two submit a bid above reserved price, and call the auction.
    ret = participant_two.submit_bid_for_auction(auction_id, 250)
    bid_id = ret["bid_id"]
    assert ret["status"] == "success"

    ret = auctioneer_one.call_auction(auction_id)
    assert ret["status"] == "success"

    # Check item summary to confirm participant_two won the auction.
    ret = auctioneer_one.query_latest_summary_for_item("iphone")
    assert ret["status"] == "success"
    assert ret["item"]["name"] == "iphone"
    assert ret["item"]["status_code"] == const.ITEM_STATUS_SOLD  # sold.
    assert ret["item"]["reserved_price"] == 200
    assert ret["auction"]["id"] == auction_id
    assert ret["auction"]["highest_bid_id"] == bid_id
    assert ret["auction"]["winning_bid_id"] == bid_id
    assert ret["auction"]["closed_at"] != None
    assert ret["prevailing_bid"]["id"] == bid_id
    assert ret["prevailing_bid"]["offer_price"] == 250
    assert ret["prevailing_bid"]["participant_id"] == participant_two.id

    # Lastly confirm we have no live auction anymore.
    assert len(participant_one.query_all_live_auctions()) == 0
