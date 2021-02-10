from abc import abstractmethod, ABCMeta


class Agent(ABCMeta('ABC', (object, ), {})):
    @abstractmethod
    def is_done(self, action_result):
        """
        Method should return a Boolean denoting whether your agent is done with
        the task or not. The 'action_result' argument should be used to inform
        your decision. 

        Note that if the value is 'ActionResult.COLLIDED' or
        'BenchBot.FINISHED', BenchBot will no longer report any available
        actions via 'BenchBot.actions' so your method needs to return True in
        these cases
        """
        return False

    @abstractmethod
    def pick_action(self, observations, action_list):
        """
        Method should return a selected action from the list provided by
        'BenchBot.actions', & a dictionary of argument values required for the
        action. The following example would move the robot forward 10cm:
            return 'move_distance', {'distance': 0.1}

        This method is also where your agent should also use the observations
        to update its semantic understanding of the world.

        The list of available actions returned from 'BenchBot.actions' will
        change based on the mode selected, & the last action_result returned by
        'BenchBot.step'. Your code below should select a valid action from the
        list, otherwise 'BenchBot.step' will throw an exception trying to
        execute an invalid action.

        The current list of possible actions (& required arguments) is
        available here:
            https://github.com/qcr/benchbot_api#default-communication-channel-list
        """
        return None

    @abstractmethod
    def save_result(self, filename, empty_results, results_format_fns):
        """
        Method should write your results for the task to the file specified by
        'filename'. The method returns no value, so if there is any failure in
        writing results an exception should be raised.

        Results must be specified in the format defined by the current task
        (see 'BenchBot.config' for details). 

        The 'empty_results' argument is pre-populated with necessary fields
        common to all results ('environment_details' & 'task_details'), as well
        as the return of the results format's 'create' function.

        The 'results_format_fns' contains all of the functions defined for that
        format, and can be useful for specialist actions (e.g. creating objects
        in scene understanding object maps).
        """
        return
