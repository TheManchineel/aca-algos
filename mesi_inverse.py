from common.file_input import open_file, read_csv
from common.mesi_algo import *
from common.misc import *
import re

def _gen_ops(cpu_cache_count: int, mem_block_count: int):
    return [
        MesiOperation(cpu_id=cid, operation_type=optype, block_id=bid)
        for cid in range(cpu_cache_count)
        for optype in MesiOperationType
        for bid in range(mem_block_count)
    ]

def _build_state_from_row(row: list[str], cpu_cache_count: int, mem_block_count: int):
    cpu_states = []
    memory_states = []
    for i in range(cpu_cache_count):
        if res := re.search(r"(?<=^Modified\()\d+(?=\))", row[i]):
            cpu_states.append(MesiCacheState(int(res.group()), MesiStateType.MODIFIED))
        elif res := re.search(r"(?<=^Exclusive\()\d+(?=\))", row[i]):
            cpu_states.append(MesiCacheState(int(res.group()), MesiStateType.EXCLUSIVE))
        elif res := re.search(r"(?<=^Shared\()\d+(?=\))", row[i]):
            cpu_states.append(MesiCacheState(int(res.group()), MesiStateType.SHARED))
        elif re.search(r"Invalid", row[i]):
            cpu_states.append(MesiCacheState(-1, MesiStateType.INVALID))
        else:
            print(row[i])
            raise ValueError("Invalid input")

    for i in range(cpu_cache_count, cpu_cache_count + mem_block_count):
        memory_states.append(from_yn(row[i]))

    return MesiSystemState(tuple(cpu_states), tuple(memory_states))

def parse_input() -> list[MesiSystemState]:
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
                    states.append(_build_state_from_row(row[2:], cpu_cache_count, mem_block_count))
        return states

def find_ops(states: list[MesiSystemState]) -> list[set[MesiOperation]]:
    all_ops = _gen_ops(cpu_cache_count=len(states[0].cpu_cache_states), mem_block_count=len(states[0].memory_state))
    return [
        {
            op for op in all_ops
            if op.apply(states[i - 1]) == states[i]
        } for i in range(1, len(states))
    ]

if __name__ == "__main__":
    states = parse_input()
    solution = find_ops(states)
    for i, ops in enumerate(solution):
        print(f"Cycle {i+1}:")
        for op in ops:
            print(f" > {op}")