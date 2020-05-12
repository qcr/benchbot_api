from abc import abstractmethod, ABCMeta


class Agent(ABCMeta('ABC', (object,), {})):

    @abstractmethod
    def is_done(self, action_result):
        """
        Method should return a Boolean denoting whether your agent is done with
        the task or not. The 'action_result' argument should be used to inform
        your decision. 

        Note that if the value is 'ActionResult.COLLIDED' or
        'ActionResult.FINISHED', BenchBot will no longer report any available
        actions via 'BenchBot.actions' so your method needs to return True in
        these cases
        """
        return False

    @abstractmethod
    def pick_action(self, observations, action_list):
        """
        Method should return a selected action from the list provided by
        'Benchbot.actions', & a dictionary of argument values required for the
        action. The following example would move the robot forward 10cm:
            return 'move_distance', {'distance': 0.1}

        This method is also where your agent should also use the observations
        to update its semantic understanding of the world.

        The list of available actions returned from 'Benchbot.actions' will
        change based on the mode selected, & the last action_result returned by
        'Benchbot.step'. Your code below should select a valid action from the
        list, otherwise 'Benchbot.step' will throw an exception trying to
        execute an invalid action.

        The current list of possible actions (& required arguments) is
        available here:
            https://github.com/roboticvisionorg/benchbot_api#default-communication-channel-list
        """
        return None

    @abstractmethod
    def save_result(self, filename, empty_results, empty_object_fn):
        """
        Method should write your results for the task to the file specified by
        'filename'. The method returns no value, so if there is any failure in
        writing results an exception should be raised.

        Results must be in our specified format to be used with the semantic
        scene understanding tools provided in the 'benchbot_eval' package. The
        results format is described in the package documentation here:
            https://github.com/roboticvisionorg/benchbot_eval#the-results-format

        The 'empty_results' & 'empty_object_fn' arguments are provided to help
        build a valid results file:
            - 'empty_results': an empty results data structure, pre-populated
              with all required BenchBot metadata (i.e. 'task_details' &
              'environment_details')
            - 'empty_object_fn': a function that generates an empty object in
              the format required for the 'objects' field of your results. The
              empty object returned by the function has all fields required
              declared & filled with blank values (as well as only providing
              'state_probs' if you are running in 'scd' mode). Simply fill the
              empty object with the data from your algorithm's object-based
              semantic map, & append it to the 'objects' field of your results.
        """
        return
