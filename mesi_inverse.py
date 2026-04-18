from common.file_input import open_file, read_csv
from common.mesi_algo import *

def _gen_ops(cpu_cache_count: int, mem_block_count: int):
    return [
        MesiOperation(cpu_id=cid, operation_type=optype, block_id=bid)
        for cid in range(cpu_cache_count)
        for optype in MesiOperationType
        for bid in range(mem_block_count)
    ]


def _parse_input() -> list[MesiSystemState]:
    with open_file() as f:
        data = read_csv(f)
        cpu_cache_count = 0
        mem_block_count = 0
        states = []
        for num, row in enumerate(data):
            match num:
                case 0:
                    constants = row[0:2]
                    if not constants == ["Cycle", "AfterOperation"]:
                        raise ValueError("Invalid input")
                    values = row[2:]
                    for value in values:
                        if value == f"P{cpu_cache_count} CacheState":
                            cpu_cache_count += 1
                        elif value == f"MemUpToDate {mem_block_count}":
                            mem_block_count += 1
                        else:
                            raise ValueError("Invalid input")
                case _:
                    states.append(MesiSystemState.from_row(row[2:], cpu_cache_count, mem_block_count))
        return states

def _find_ops(states: list[MesiSystemState]) -> list[set[MesiOperation]]:
    all_ops = _gen_ops(cpu_cache_count=len(states[0].cpu_cache_states), mem_block_count=len(states[0].memory_state))
    return [
        {
            op for op in all_ops
            if op.apply(states[i - 1]) == states[i]
        } for i in range(1, len(states))
    ]

if __name__ == "__main__":
    states = _parse_input()
    solution = _find_ops(states)
    for i, ops in enumerate(solution):
        print(f"Cycle {i+1}:")
        for op in ops:
            print(f" > {op}")