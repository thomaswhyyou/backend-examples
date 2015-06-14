import customutils


if __name__ == "__main__":
    test_list = [1, 2, 3, 5, 10, 9, 8, 9, 10, 11, 7]
    assert customutils.find_consecutive_runs(test_list) == [0, 4, 6, 7]

    test_list = [1, 2, 3, 1, 1, 2, 3, 1, 20, 19, 18, 17, 99, 100, 101, 100, 99]
    assert customutils.find_consecutive_runs(test_list) == [0, 4, 8, 9, 12, 14]
