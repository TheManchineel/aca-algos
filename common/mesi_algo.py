import re
from dataclasses import dataclass
from enum import Enum

from common.misc import from_yn


class MesiStateType(Enum):
    EXCLUSIVE = 0
    SHARED = 1
    MODIFIED = 2
    INVALID = 3

class MesiOperationType(Enum):
    READ = 0
    WRITE = 1

@dataclass(frozen=True)
class MesiCacheState:
    block_id: int
    state: MesiStateType

    def __str__(self):
        return f"{self.state.name.capitalize()}({self.block_id})"

    def __repr__(self):
        return self.__str__()

@dataclass(frozen=True)
class MesiSystemState:
    cpu_cache_states: tuple[MesiCacheState, ...]
    memory_state: tuple[bool, ...]

    @staticmethod
    def from_row(
        row: list[str], cpu_cache_count: int, mem_block_count: int
    ):
        cpu_states = []
        memory_states = []
        for i in range(cpu_cache_count):
            if res := re.search(r"(?<=^Modified\()\d+(?=\))", row[i]):
                cpu_states.append(
                    MesiCacheState(int(res.group()), MesiStateType.MODIFIED)
                )
            elif res := re.search(r"(?<=^Exclusive\()\d+(?=\))", row[i]):
                cpu_states.append(
                    MesiCacheState(int(res.group()), MesiStateType.EXCLUSIVE)
                )
            elif res := re.search(r"(?<=^Shared\()\d+(?=\))", row[i]):
                cpu_states.append(
                    MesiCacheState(int(res.group()), MesiStateType.SHARED)
                )
            elif re.search(r"Invalid", row[i]):
                cpu_states.append(MesiCacheState(-1, MesiStateType.INVALID))
            else:
                print(row[i])
                raise ValueError("Invalid input")

        for i in range(cpu_cache_count, cpu_cache_count + mem_block_count):
            memory_states.append(from_yn(row[i]))

        return MesiSystemState(tuple(cpu_states), tuple(memory_states))


def _evict_local(
    cpu_id: int, cpu_states: list[MesiCacheState], memory_uptodate_states: list[bool]
):
    current_state = cpu_states[cpu_id]
    if current_state.block_id == -1:
        return

    if current_state.state == MesiStateType.MODIFIED:
        memory_uptodate_states[current_state.block_id] = True

    cpu_states[cpu_id] = MesiCacheState(-1, MesiStateType.INVALID)


def _access_read(
    block_id: int,
    cpu_id: int,
    cpu_states: list[MesiCacheState],
    memory_uptodate_states: list[bool],
):
    other_cpus_with_block = [
        i
        for i in range(len(cpu_states))
        if cpu_states[i].block_id == block_id and i != cpu_id
    ]

    shared_found = False

    for other_cpu in other_cpus_with_block:
        st = cpu_states[other_cpu].state
        if st == MesiStateType.MODIFIED:
            memory_uptodate_states[block_id] = True
            cpu_states[other_cpu] = MesiCacheState(block_id, MesiStateType.SHARED)
            shared_found = True
        elif st in (MesiStateType.EXCLUSIVE, MesiStateType.SHARED):
            cpu_states[other_cpu] = MesiCacheState(block_id, MesiStateType.SHARED)
            shared_found = True

    new_state = MesiStateType.SHARED if shared_found else MesiStateType.EXCLUSIVE
    cpu_states[cpu_id] = MesiCacheState(block_id, new_state)


def _access_write(
    block_id: int,
    cpu_id: int,
    cpu_states: list[MesiCacheState],
    memory_uptodate_states: list[bool],
):
    other_cpus_with_block = [
        i
        for i in range(len(cpu_states))
        if cpu_states[i].block_id == block_id and i != cpu_id
    ]

    for other_cpu in other_cpus_with_block:
        st = cpu_states[other_cpu].state
        if st == MesiStateType.MODIFIED:
            memory_uptodate_states[block_id] = True

        cpu_states[other_cpu] = MesiCacheState(-1, MesiStateType.INVALID)

    memory_uptodate_states[block_id] = False
    cpu_states[cpu_id] = MesiCacheState(block_id, MesiStateType.MODIFIED)


@dataclass(frozen=True)
class MesiOperation:
    cpu_id: int
    operation_type: MesiOperationType
    block_id: int

    def apply(self, system_state: MesiSystemState):
        prev_cpu_cache_states = list(system_state.cpu_cache_states)
        prev_memory_state = list(system_state.memory_state)

        current_cpu_cache_state = prev_cpu_cache_states[self.cpu_id]

        match self.operation_type:
            case MesiOperationType.READ:
                if current_cpu_cache_state.block_id != self.block_id:
                    _evict_local(self.cpu_id, prev_cpu_cache_states, prev_memory_state)
                _access_read(
                    self.block_id, self.cpu_id, prev_cpu_cache_states, prev_memory_state
                )

            case MesiOperationType.WRITE:
                if current_cpu_cache_state.block_id != self.block_id:
                    _evict_local(self.cpu_id, prev_cpu_cache_states, prev_memory_state)
                _access_write(
                    self.block_id, self.cpu_id, prev_cpu_cache_states, prev_memory_state
                )

        return MesiSystemState(tuple(prev_cpu_cache_states), tuple(prev_memory_state))

    def __str__(self):
        return (
            f"P{self.cpu_id}: {self.operation_type.name.lower()} block {self.block_id}"
        )

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def from_repr(text: str):
        res = re.search(r"P(\d+): (\w+) block (\d+)", text)
        if not res:
            raise ValueError("Invalid input")

        cpu_id, operation_type, block_id = res.groups()
        return MesiOperation(int(cpu_id), MesiOperationType[operation_type.upper()], int(block_id))