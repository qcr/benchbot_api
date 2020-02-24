from abc import abstractmethod


class Agent(object):

    @abstractmethod
    def is_done(self, action_result):
        """
        Method should return a Boolean denoting whether your agent is done with
        the task or not. The 'action_result' argument should be used to inform
        your decision. 

        Note that if the value is 'ActionResult.COLLIDED' or
        'ActionResult.FINISHED', BenchBot will no longer report any available
        actions via 'BenchBot.actions' so your method should definitely return
        True in these cases
        """
        return False

    @abstractmethod
    def pick_action(self, observations):
        """
        Method should return a selected action from the list provided by
        'Benchbot.actions', & a dictionary of argument values required for the
        action. The follwoing example would move the robot forward 10cm:
            return 'move_distance', {'distance': 0.1}

        The list of available actions returned from 'Benchbot.actions' will
        change based on the mode selected, & the last action_result returned by
        'Benchbot.step'. Your code below should select a valid action from the
        list, otherwise 'Benchbot.step' will throw an exception trying to
        execute an invalid action.

        The current list of possible actions (& required arguments) are:
            TODO
        """
        return None

    @abstractmethod
    def save_result(self, filename):
        """
        Method should write your results for the task to the file specified by
        'filename'. The method returns no value, so if there is any failure in
        writing results an exception should be raised.

        To use results with the semantic scene understanding tools provided by
        'benchbot_eval', they must be in the format specified 
        TODO TIDY THIS UP / MAKE IT ACCURATE!
        """
        return
