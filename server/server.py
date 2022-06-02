from contextlib import suppress
import threading
import time
from typing import Optional, List

from pygls import *
from pygls.lsp.methods import (
    HOVER,
    SET_TRACE_NOTIFICATION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS,
)
from pygls.lsp.types import (
    ConfigurationItem,
    ConfigurationParams,
    Diagnostic,
    DiagnosticSeverity,
    DidChangeTextDocumentParams,
    Hover,
    MarkupContent,
    Position,
    Range,
    Range,
    TextDocumentPositionParams,
)
from pygls.server import LanguageServer
from qchecker.match import TextRange
from qchecker.substructures import SUBSTRUCTURES
from qchecker.parser import CodeModule

EXTENSION_NAME = "Stylezilla"
SECONDS_BETWEEN_UPDATE = 3


class PythonLanguageServer(LanguageServer):
    CONFIGURATION_SECTION = 'stylezilla'
    HOVER = 'textDocument/hover'

    def __init__(self):
        super().__init__()
        self.current_matches = []
        self.last_document = None
        self.last_document_uri = None
        self.did_change = True
        self.config_did_change = True
        self.substructures = []
        run_continuously(self)


def run_continuously(ls, interval=3):
    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                cls.check_config()
                cls.check_code()
                time.sleep(SECONDS_BETWEEN_UPDATE)

        @classmethod
        def check_config(cls):
            ls.show_message_log("Checking Config")
            if ls.config_did_change:
                ls.show_message_log("Config did change")
                ls.config_did_change = False
                ls.did_change = True
                get_configuration(ls)

        @classmethod
        def check_code(cls):
            ls.show_message_log("Checking Document")
            if ls.last_document is not None and ls.did_change:
                with suppress(SyntaxError):
                    module = CodeModule(ls.last_document)
                    matches = _get_matches(module, ls.substructures)
                    ls.current_matches = matches
                    publish_diagnostics(ls)
                    diagnostics = _make_diagnostics(ls.current_matches)
                    publish_diagnostics(ls, diagnostics)
                    ls.did_change = False
                    ls.show_message_log("Document Did Change")

    continuous_thread = ScheduleThread()
    continuous_thread.start()
    return cease_continuous_run


stylezilla_server = PythonLanguageServer()


@stylezilla_server.feature(HOVER)
def hover(ls, params: TextDocumentPositionParams) -> Optional[Hover]:
    cursor_position = TextRange(
        params.position.line + 1,
        params.position.character
    )
    for match in ls.current_matches:
        if match.text_range.contains(cursor_position):
            description = match.description.content
            description_markup = match.description.markup.value
            contents = MarkupContent(
                kind=description_markup, value=description)
            return Hover(contents=contents)


@stylezilla_server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls, params: DidChangeTextDocumentParams):
    """Text document did change notification."""
    ls.did_change = True
    text_doc = ls.workspace.get_document(params.text_document.uri)
    ls.last_document = text_doc.source
    ls.show_message_log(ls.last_document)
    ls.last_document_uri = params.text_document.uri


@stylezilla_server.feature(TEXT_DOCUMENT_DID_OPEN)
def did_open(ls, params):
    """Text document did change notification."""
    get_configuration(ls)
    ls.did_change = True
    text_doc = ls.workspace.get_document(params.text_document.uri)
    ls.last_document = text_doc.source
    ls.last_document_uri = params.text_document.uri


@stylezilla_server.feature(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
def publish_diagnostics(ls, diagnostics=[]):
    ls.publish_diagnostics(ls.last_document_uri, diagnostics)


@stylezilla_server.feature(SET_TRACE_NOTIFICATION)
def get_configuration(ls, params=None):
    ls.get_configuration(
        ConfigurationParams(
            items=[ConfigurationItem(
                section=f"{EXTENSION_NAME}.substructures")]
        ),
        lambda config, ls=ls: set_config(config[0], ls)
    )


def set_config(config, ls):
    substructure_names = {
        substructure.__name__: substructure for substructure in SUBSTRUCTURES
    }
    active = []
    for name, value in config.items():
        if value:
            active.append(substructure_names[name])
    if ls.substructures != active:
        ls.config_did_change = True
        ls.substructures = active


def _validate(ls, params):
    diagnostics = _make_diagnostics(ls.current_matches)
    publish_diagnostics(ls, params, diagnostics)


def _get_matches(module, substructures):
    matches = []
    for substructure in substructures:
        matches += substructure.iter_matches(module)
    return matches


def _make_diagnostics(matches):
    diagnostics = []
    for match in matches:
        text_range = match.text_range
        d = Diagnostic(
            range=Range(
                start=Position(
                    line=text_range.from_line - 1,
                    character=text_range.from_offset,
                ),
                end=Position(
                    line=text_range.to_line - 1,
                    character=text_range.to_offset,
                )
            ),
            message=match.id,
            source=EXTENSION_NAME,
            severity=DiagnosticSeverity.Warning,
        )
        diagnostics.append(d)
    return diagnostics
