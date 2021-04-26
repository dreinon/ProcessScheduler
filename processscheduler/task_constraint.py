"""Task constraints and related classes."""

# Copyright (c) 2020-2021 Thomas Paviot (tpaviot@gmail.com)
#
# This file is part of ProcessScheduler.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.

from typing import Optional

from z3 import And, Bool, Not, BoolRef, Implies, If, Or, Xor, PbEq, PbGe, PbLe

from processscheduler.base import _Constraint

#
# Task constraints base class
#
class _TaskConstraint(_Constraint):
    """ abstract class for task constraint.

    Task constraints only apply for scheduled tasks. If an optional
    task is not scheduled, then the constraint does not apply.
    """
    pass

#
# Tasks constraints for two or more classes
#
class TaskPrecedence(_TaskConstraint):
    """ Task precedence relation """
    def __init__(self, task_before, task_after,
                 offset=0, kind='lax',
                 optional: Optional[bool] = False):
        """ kind might be either LAX/STRICT/TIGHT
        Semantics : task after will start at least after offset periods
        task_before is finished.
        LAX constraint: task1_before_end + offset <= task_after_start
        STRICT constraint: task1_before_end + offset < task_after_start
        TIGHT constraint: task1_before_end + offset == task_after_start
        """
        super().__init__()

        if kind not in ['lax', 'strict', 'tight']:
            raise ValueError("kind must either be 'lax', 'strict' or 'tight'")

        if not isinstance(offset, int) or offset < 0:
            raise ValueError('offset must be a positive integer')

        self.optional = optional
        self.offset = offset
        self.kind = kind

        if offset > 0:
            lower = task_before.end + offset
        else:
            lower = task_before.end
        upper = task_after.start

        if kind == 'lax':
            scheduled_assertion = lower <= upper
        elif kind == 'strict':
            scheduled_assertion = lower < upper
        else: # kind == 'tight':
            scheduled_assertion = lower == upper

        if task_before.optional or task_after.optional:
            # both tasks must be scheduled so that the precedence constraint applies
            self.set_applied_not_applied_assertions(Implies(And(task_before.scheduled, task_after.scheduled) , scheduled_assertion))
        else:
            self.set_applied_not_applied_assertions(scheduled_assertion)

class TasksStartSynced(_TaskConstraint):
    """ Two tasks that must start at the same time """
    def __init__(self, task_1, task_2, optional: Optional[bool] = False) -> None:
        super().__init__()

        scheduled_assertion = task_1.start == task_2.start

        self.optional = optional

        if task_1.optional or task_2.optional:
            # both tasks must be scheduled so that the startsynced constraint applies
            self.set_applied_not_applied_assertions(Implies(And(task_1.scheduled, task_2.scheduled)
                                       , scheduled_assertion))
        else:
            self.set_applied_not_applied_assertions(scheduled_assertion)

class TasksEndSynced(_TaskConstraint):
    """ Two tasks that must complete at the same time """
    def __init__(self, task_1, task_2, optional: Optional[bool] = False) -> None:
        super().__init__()

        scheduled_assertion = task_1.end == task_2.end

        self.optional = optional

        if task_1.optional or task_2.optional:
            # both tasks must be scheduled so that the endsynced constraint applies
            self.set_applied_not_applied_assertions(Implies(And(task_1.scheduled, task_2.scheduled) , scheduled_assertion))
        else:
            self.set_applied_not_applied_assertions(scheduled_assertion)

class TasksDontOverlap(_TaskConstraint):
    """ two tasks must not overlap, i.e. one needs to be completed before
    the other can be processed """
    def __init__(self, task_1, task_2, optional: Optional[bool] = False) -> None:
        super().__init__()

        self.optional = optional

        scheduled_assertion = Xor(task_2.start >= task_1.end,
                                  task_1.start >= task_2.end)

        if task_1.optional or task_2.optional:
            # if one task is not scheduledboth tasks must be scheduled so that the not overlap constraint applies
            self.set_applied_not_applied_assertions(Implies(And(task_1.scheduled, task_2.scheduled) , scheduled_assertion))
        else:
            self.set_applied_not_applied_assertions(scheduled_assertion)

#
# Task constraints for one single task
#
class TaskStartAt(_TaskConstraint):
    """ One task must start at the desired time """
    def __init__(self, task, value: int, optional: Optional[bool] = False) -> None:
        super().__init__()
        self.value = value

        self.optional = optional

        scheduled_assertion = task.start == value

        if task.optional:
            self.set_applied_not_applied_assertions(Implies(task.scheduled, scheduled_assertion))
        else:
            self.set_applied_not_applied_assertions(scheduled_assertion)

class TaskStartAfterStrict(_TaskConstraint):
    """ task.start > value """
    def __init__(self, task, value: int, optional: Optional[bool] = False) -> None:
        super().__init__()
        self.value = value

        self.optional = optional

        scheduled_assertion = task.start > value

        if task.optional:
            self.set_applied_not_applied_assertions(Implies(task.scheduled, scheduled_assertion))
        else:
            self.set_applied_not_applied_assertions(scheduled_assertion)

class TaskStartAfterLax(_TaskConstraint):
    """  task.start >= value  """
    def __init__(self, task, value: int, optional: Optional[bool] = False) -> None:
        super().__init__()
        self.value = value

        self.optional = optional

        scheduled_assertion = task.start >= value

        if task.optional:
            self.set_applied_not_applied_assertions(Implies(task.scheduled, scheduled_assertion))
        else:
            self.set_applied_not_applied_assertions(scheduled_assertion)

class TaskEndAt(_TaskConstraint):
    """ On task must complete at the desired time """
    def __init__(self, task, value: int, optional: Optional[bool] = False) -> None:
        super().__init__()
        self.value = value

        self.optional = optional

        scheduled_assertion = task.end == value

        if task.optional:
            self.set_applied_not_applied_assertions(Implies(task.scheduled, scheduled_assertion))
        else:
            self.set_applied_not_applied_assertions(scheduled_assertion)

class TaskEndBeforeStrict(_TaskConstraint):
    """ task.end < value """
    def __init__(self, task, value: int, optional: Optional[bool] = False) -> None:
        super().__init__()
        self.value = value

        self.optional = optional

        scheduled_assertion = task.end < value

        if task.optional:
            self.set_applied_not_applied_assertions(Implies(task.scheduled, scheduled_assertion))
        else:
            self.set_applied_not_applied_assertions(scheduled_assertion)

class TaskEndBeforeLax(_TaskConstraint):
    """ task.end <= value """
    def __init__(self, task, value: int, optional: Optional[bool] = False) -> None:
        super().__init__()
        self.value = value

        self.optional = optional

        scheduled_assertion = task.end <= value

        if task.optional:
            self.set_applied_not_applied_assertions(Implies(task.scheduled, scheduled_assertion))
        else:
            self.set_applied_not_applied_assertions(scheduled_assertion)
#
# Optional classes only constraints
#
class OptionalTaskConditionSchedule(_TaskConstraint):
    """An optional task that is scheduled only if a condition is fulfilled."""
    def __init__(self, task, condition: BoolRef, optional: Optional[bool] = False) -> None:
        super().__init__()

        self.optional = optional

        if not task.optional:
            raise TypeError('Task %s must be optional.' % task.name)

        self.set_applied_not_applied_assertions(Implies(condition, task.scheduled))

class OptionalTasksDependency(_TaskConstraint):
    """task_2 is scheduled if and only if task_1 is scheduled"""
    def __init__(self, task_1, task_2, optional: Optional[bool] = False) -> None:
        super().__init__()

        self.optional = optional

        if not task_2.optional:
            raise TypeError('Task %s must be optional.' % task_2.name)

        self.set_applied_not_applied_assertions(Implies(task_1.scheduled, task_2.scheduled))

class ForceScheduleNOptionalTasks(_TaskConstraint):
    """Given a set of m different optional tasks, force the solver to schedule
    at at least/at most/exactly n tasks, with 0 < n <= m."""
    def __init__(self, list_of_optional_tasks,
                       nb_tasks_to_schedule: Optional[int] = 1,
                       kind: Optional[str] = 'exact',
                       optional: Optional[bool] = False) -> None:
        super().__init__()

        self.optional = optional

        problem_function = {'atleast': PbGe, 'atmost': PbLe, 'exact': PbEq}

        # first check that all tasks from the list_of_optional_tasks are
        # actually optional
        for task in list_of_optional_tasks:
            if not task.optional:
                raise TypeError('This class %s must excplicitly be set as optional.' % task.name)
        # all scheduled variables to take into account
        sched_vars = []
        for task in list_of_optional_tasks:
            sched_vars.append(task.scheduled)

        asst = problem_function[kind]([(scheduled, True) for scheduled in sched_vars],
                                      nb_tasks_to_schedule)
        self.set_applied_not_applied_assertions(asst)

class ScheduleNTasksInTimeIntervals(_TaskConstraint):
    """Given a set of m different tasks, and a list of time intervals, schedule N tasks among m
    in this time interval"""
    def __init__(self, list_of_tasks,
                       nb_tasks_to_schedule,
                       list_of_time_intervals,
                       kind: Optional[str] = 'exact',
                       optional: Optional[bool] = False) -> None:
        super().__init__()

        self.optional = optional

        problem_function = {'atleast': PbGe, 'atmost': PbLe, 'exact': PbEq}

        # first check that all tasks from the list_of_optional_tasks are
        # actually optional
        if not isinstance(list_of_tasks, list):
            raise TypeError('list_of_task must be a list')

        if not isinstance(list_of_time_intervals, list):
            raise TypeError('list_of_time_intervals must be a list of list')

        # check for special case
        # for the first interval, it is a bit special: if the lower bound is different
        # from zero, we have to handle the case where the start and/or end are scheduled
        # before the first allowed interval
        first_interval = list_of_time_intervals[0]
        lower_bound_first_interval = first_interval[0]
        is_first_bound_greater_than_zero = False
        if lower_bound_first_interval > 0:
            is_first_bound_greater_than_zero = True

        # count the number of tasks that re scheduled in this time interval
        all_bools =[]
        for task in list_of_tasks:
            # for this task, the logic expression is that any of its start or end must be
            # between two consecutive intervals
            i = 0
            b = Bool('InTimeIntervalTask_%s_%i' % (task.name, i))
            cstrs = []
            for time_interval in list_of_time_intervals:
                lower_bound, upper_bound = time_interval
                cstrs += [task.start >= lower_bound, task.end <= upper_bound,
                             Not(And(task.start < lower_bound, task.end > lower_bound)),  # overlap at start
                             Not(And(task.start < upper_bound, task.end > upper_bound)),   # overlap at end
                             Not(And(task.start < lower_bound, task.end > upper_bound))]   # full overlap
            asst = Implies(b, And(cstrs))
            self.set_applied_not_applied_assertions(asst)
            all_bools.append(b)

        # we also have to exclude all the other cases, where start or end can be between two intervals
        # then set the constraint for the number of tasks to schedule
        asst_pb = problem_function[kind]([(scheduled, True) for scheduled in all_bools],
                                          nb_tasks_to_schedule)
        self.set_applied_not_applied_assertions(asst_pb)
