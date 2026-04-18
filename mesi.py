from typing import List

from common.file_input import open_file, read_csv
from common.mesi_algo import *

def _parse_input() -> tuple[MesiSystemState, list[MesiOperation]]:
    with open_file() as f:
        data = read_csv(f)
        cpu_cache_count = 0
        mem_block_count = 0
        ops = []
        for num, row in enumerate(data):
            match num:
                case 0:
                    constants = row[0:2]
                    if not constants == ["Cycle", "Operation"]:
                        raise ValueError("Invalid input")
                    values = row[2:]
                    for value in values:
                        if value == f"P{cpu_cache_count} CacheState":
                            cpu_cache_count += 1
                        elif value == f"MemUpToDate {mem_block_count}":
                            mem_block_count += 1
                        else:
                            raise ValueError("Invalid input")
                case 1:
                    initial_state = MesiSystemState.from_row(row[2:], cpu_cache_count, mem_block_count)
                case _:
                    ops.append(MesiOperation.from_repr(row[1]))
        return initial_state, ops

def _run_algo(initial_state: MesiSystemState, ops: list[MesiOperation]) -> list[MesiSystemState]:
    intermediate_states = [initial_state]
    for op in ops:
        intermediate_states.append(op.apply(intermediate_states[-1]))
    return intermediate_states

if __name__ == "__main__":
    initial_state, ops = _parse_input()

    print(ops)
    states = _run_algo(initial_state, ops)
    for state in states:
        print(state)