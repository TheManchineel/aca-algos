from copy import deepcopy
from dataclasses import dataclass
from enum import Enum

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

@dataclass(frozen=True)
class MesiSystemState:
    cpu_cache_states: tuple[MesiCacheState]
    memory_state: tuple[bool]


def _release(block_id: int, cpu_states: list[MesiCacheState], memory_uptodate_states: list[bool], invalidate: bool = False):
    if block_id == -1:
        return
    try:
        cpus_using = [i for i in range(len(cpu_states)) if cpu_states[i].block_id == block_id]
        memory_uptodate_states[block_id] = True
        target_state = MesiStateType.INVALID if invalidate else MesiStateType.EXCLUSIVE if len(cpus_using) == 1 else MesiStateType.SHARED
        target_cache = -1 if invalidate else block_id
        for cpu_id in cpus_using:
            if cpu_states[cpu_id].state == MesiStateType.MODIFIED or cpu_states[cpu_id].state == MesiStateType.EXCLUSIVE:
                cpu_states[cpu_id] = MesiCacheState(target_cache, target_state)
    except ValueError:
        return

def _access_read(block_id: int, cpu_id: int, cpu_states: list[MesiCacheState], memory_uptodate_states: list[bool]):
    if block_id == -1:
        raise ValueError("Invalid block id")
    cpus_exclusive = [i for i in range(len(cpu_states)) if cpu_states[i].block_id == block_id and cpu_states[i].state == MesiStateType.EXCLUSIVE]
    cpus_shared = [i for i in range(len(cpu_states)) if cpu_states[i].block_id == block_id and cpu_states[i].state == MesiStateType.SHARED]
    cpus_modified = [i for i in range(len(cpu_states)) if cpu_states[i].block_id == block_id and cpu_states[i].state == MesiStateType.MODIFIED]
    if cpus_shared:
        cpu_states[cpu_id] = MesiCacheState(block_id, MesiStateType.SHARED)
    elif cpus_exclusive and cpus_exclusive[0] != cpu_id:
        cpu_states[cpus_exclusive[0]] = MesiCacheState(block_id, MesiStateType.SHARED)
        cpu_states[cpu_id] = MesiCacheState(block_id, MesiStateType.SHARED)
    elif cpus_modified and cpus_modified[0] != cpu_id:
            _release(block_id, cpu_states, memory_uptodate_states, invalidate=False)
            for cpu_id2 in cpus_modified:
                cpu_states[cpu_id2] = MesiCacheState(block_id, MesiStateType.SHARED)
            cpu_states[cpu_id] = MesiCacheState(block_id, MesiStateType.SHARED)
    else:
        cpu_states[cpu_id] = MesiCacheState(block_id, MesiStateType.EXCLUSIVE)

def _access_write(block_id: int, cpu_id: int, cpu_states: list[MesiCacheState], memory_uptodate_states: list[bool]):
    if block_id == -1:
        raise ValueError("Invalid block id")
    cpus_exclusive = [i for i in range(len(cpu_states)) if cpu_states[i].block_id == block_id and cpu_states[i].state == MesiStateType.EXCLUSIVE]
    cpus_shared = [i for i in range(len(cpu_states)) if cpu_states[i].block_id == block_id and cpu_states[i].state == MesiStateType.SHARED]
    cpus_modified = [i for i in range(len(cpu_states)) if cpu_states[i].block_id == block_id and cpu_states[i].state == MesiStateType.MODIFIED]

    if cpus_exclusive and cpus_exclusive[0] != cpu_id:
        _release(block_id, cpu_states, memory_uptodate_states, invalidate=True)
    elif cpus_shared:
        _release(block_id, cpu_states, memory_uptodate_states, invalidate=True)
    elif cpus_modified and cpus_modified[0] != cpu_id:
        _release(block_id, cpu_states, memory_uptodate_states, invalidate=True)

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
                if current_cpu_cache_state.block_id == self.block_id:
                    pass
                else:
                    _release(current_cpu_cache_state.block_id, prev_cpu_cache_states, prev_memory_state, invalidate=True)
                    _access_read(self.block_id, self.cpu_id, prev_cpu_cache_states, prev_memory_state)
            case MesiOperationType.WRITE:
                if current_cpu_cache_state.block_id != self.block_id:
                    _release(current_cpu_cache_state.block_id, prev_cpu_cache_states, prev_memory_state,invalidate=True)

                _access_write(self.block_id, self.cpu_id, prev_cpu_cache_states, prev_memory_state)
        return MesiSystemState(tuple(prev_cpu_cache_states), tuple(prev_memory_state))

    def __str__(self):
        return f"P{self.cpu_id}: {self.operation_type.name.lower()} block {self.block_id}"