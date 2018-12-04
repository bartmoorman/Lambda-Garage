# -*- coding: utf-8 -*-

# This is the Garage Alexa Skill, built using
# the implementation of handler classes approach in skill builder.
import logging
import requests
import os

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name

from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard

# Skill Builder object
sb = SkillBuilder()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


PHRASES = {
    "welcome": "Hello! Welcome to the Garage.",
    "goodbye": "Goodbye!",
    "help": "You can say something like open the door, or is the door closed?",
    "no_help": "The Garage skill can't help you with that!",
    "action_response": {
        "complete": "{}, the door is {}.",
        "nothing_to_do": "{}, it's already {}."
    },
    "decision": {
        "ok": "Ok",
        "yes": "Yes",
        "no": "No"
    },
    "status_response": "{}, it's {}.",
    "problem_connecting": "Sorry, there was a problem connecting to the Garage.",
    "problem_response": "Sorry, there was a problem with the response I received.",
    "problem_terrible": "Sorry, something went terribly wrong.",
    "problem_unknown": "Sorry, there was an unknown problem."

}
STATUSES = {
    0: "open",
    1: "closed"
}
ACTIONS = {
    "status": {
        0: "open",
        1: "close"
    },
    "response": {
        0: "closing",
        1: "opening"
    }
}


# Request Handler classes
class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = PHRASES["welcome"]

        handler_input.response_builder.speak(speech_text).set_should_end_session(False)
        return handler_input.response_builder.response


class ActionIntentHandler(AbstractRequestHandler):
    """Handler for Action Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("ActionIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        request = handler_input.request_envelope.request
        spayload={'func': 'getPosition', 'token': os.getenv('GARAGE_TOKEN'), 'device': 'sensor'}
        sr = requests.post(os.getenv('GARAGE_HOST') + '/src/action.php', data=spayload)

        if sr.status_code == 200:
            sdata = sr.json()

            if sdata["success"]:
                if int(sdata["data"]) == 0 or int(sdata["data"]) == 1:
                    status = ACTIONS["status"][int(sdata["data"])]
                    if status != request.intent.slots["action"].value:
                        apayload={'func': 'doActivate', 'token': os.getenv('GARAGE_TOKEN'), 'device': 'opener'}
                        ar = requests.post(os.getenv('GARAGE_HOST') + '/src/action.php', data=apayload)

                        if ar.status_code == 200:
                            adata = ar.json()

                            if adata["success"]:
                                speech_text = PHRASES["action_response"]["complete"].format(PHRASES["decision"]["ok"], ACTIONS["response"][int(sdata["data"])])
                            else:
                                speech_text = PHRASES["problem_response"]
                        else:
                            speech_text = PHRASES["problem_connecting"]
                    else:
                        speech_text = PHRASES["action_response"]["nothing_to_do"].format(PHRASES["decision"]["no"], STATUSES[int(sdata["data"])])
                else:
                    speech_text = PHRASES["problem_terrible"]
            else:
                speech_text = PHRASES["problem_response"]
        else:
            speech_text = PHRASES["problem_connecting"]

        handler_input.response_builder.speak(speech_text).set_should_end_session(True)
        return handler_input.response_builder.response


class StatusIntentHandler(AbstractRequestHandler):
    """Handler for Status Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("StatusIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        request = handler_input.request_envelope.request
        spayload={'func': 'getPosition', 'token': os.getenv('GARAGE_TOKEN'), 'device': 'sensor'}
        sr = requests.post(os.getenv('GARAGE_HOST') + '/src/action.php', data=spayload)

        if sr.status_code == 200:
            sdata = sr.json()

            if sdata["success"]:
                if int(sdata["data"]) == 0 or int(sdata["data"]) == 1:
                    status = STATUSES[int(sdata["data"])]
                    decision = PHRASES["decision"]["yes"] if status == request.intent.slots["status"].value else PHRASES["decision"]["no"]
                    speech_text = PHRASES["status_response"].format(decision, status)
                else:
                    speech_text = PHRASES["problem_terrible"]
            else:
                speech_text = PHRASES["problem_response"]
        else:
            speech_text = PHRASES["problem_connecting"]

        handler_input.response_builder.speak(speech_text).set_should_end_session(True)
        return handler_input.response_builder.response


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = PHRASES["help"]

        handler_input.response_builder.speak(speech_text).ask(speech_text)
        return handler_input.response_builder.response


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = PHRASES["goodbye"]

        handler_input.response_builder.speak(speech_text)
        return handler_input.response_builder.response


class FallbackIntentHandler(AbstractRequestHandler):
    """AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = PHRASES["no_help"]
        reprompt = PHRASES["help"]

        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        return handler_input.response_builder.response


# Exception Handler classes
class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speech = PHRASES["problem_unknown"]
        handler_input.response_builder.speak(speech).ask(speech)

        return handler_input.response_builder.response


# Add all request handlers to the skill.
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(ActionIntentHandler())
sb.add_request_handler(StatusIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# Add exception handler to the skill.
sb.add_exception_handler(CatchAllExceptionHandler())

# Expose the lambda handler to register in AWS Lambda.
lambda_handler = sb.lambda_handler()
