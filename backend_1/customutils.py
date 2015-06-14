# Assume given data is clean, i.e. always list of positive integers.
def find_consecutive_runs(numbers, run_length=3):

    found_indexes = []

    for start in range(len(numbers)):
        end = start + run_length
        target_slice = numbers[start:end]

        if len(target_slice) < run_length:
            # Ran out of numbers to make the run; no point in going further.
            break

        sorted_slice_asc = sorted(numbers[start:end])
        sorted_slice_desc = sorted(numbers[start:end], reverse=True)
        if not (target_slice == sorted_slice_asc or
                target_slice == sorted_slice_desc):
            # Order changed either direction, not consecutive.
            continue

        consec_counter = 0
        for idx, current_number in enumerate(sorted_slice_asc[:-1]):
            next_number = sorted_slice_asc[idx+1]
            if next_number - current_number == 1:
                consec_counter += 1
            else:
                break

        if consec_counter + 1 == run_length:
            found_indexes.append(start)

    return found_indexes or None
