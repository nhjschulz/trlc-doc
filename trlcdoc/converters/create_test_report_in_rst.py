"""Project specific Markdown converter functions.

    Author: Andreas Merkle (andreas.merkle@newtec.de)
"""

# pyTRLCConverter - A tool to convert TRLC files to specific formats.
# Copyright (c) 2024 - 2026 NewTec GmbH
#
# This file is part of pyTRLCConverter program.
#
# The pyTRLCConverter program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# The pyTRLCConverter program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with pyTRLCConverter.
# If not, see <https://www.gnu.org/licenses/>.

# Imports **********************************************************************
from typing import Optional, Any
from pyTRLCConverter.base_converter import RecordsPolicy
from pyTRLCConverter.ret import Ret
from pyTRLCConverter.rst_converter import RstConverter
from pyTRLCConverter.rst.element import RstRawText, RstTable
from pyTRLCConverter.rst.text import RstText
from pyTRLCConverter.trlc_helper import Record_Object

# Variables ********************************************************************

TEST_CASES_FILE_NAME = "swe-test.rst"

# Role for inline raw HTML. A table row can't hold a label, so each row gets an anchor as HTML span.
# The empty comment ends the directive, otherwise the indented table would become its content.
RAW_HTML_ROLE = ".. role:: raw-html(raw)\n   :format: html\n\n..\n\n"

# Classes **********************************************************************


class CustomRstConverter(RstConverter):
    # lobster-trace: SwRequirements.sw_req_builtin_converters
    """Custom Project specific reStructuredText converter responsible for converting the
        SW test case results into reStructuredText format.
    """

    def __init__(self, args: Any) -> None:
        """Initializes the converter.

        Args:
            args (Any): The parsed program arguments.
        """
        super().__init__(args)

        # Set project specific record handlers for the converter.
        self._set_project_record_handlers(
           {
            "SwTestCaseResult": self._append_test_case_result
           }
        )

        self._record_policy = RecordsPolicy.RECORD_SKIP_UNDEFINED

        self._test_case_results = []

    @staticmethod
    def get_description() -> str:
        """ Return converter description.

         Returns:
            str: Converter description
        """
        return "Convert SW test case results to reStructuredText format."

    def leave_file(self, file_name: str) -> Ret:
        """
        Leave a file.

        Args:
            file_name (str): File name

        Returns:
            Ret: Status
        """

        # Multiple document mode?
        if self._args.single_document is False:
            assert self._document is not None
            self._print_test_case_results()

        return super().leave_file(file_name)

    # pylint: disable=unused-argument
    def _append_test_case_result(self, record: Record_Object, level: int, translation: Optional[dict]) -> Ret:
        """
        Append test case result.

        Args:
            record (Record_Object): Record object to convert.
            level (int): Current level of the record object.
            translation (Optional[dict]): Translation dictionary for the record object.
                                            If None, no translation is applied.

        Returns:
            Ret: Status
        """
        self._test_case_results.append(record)
        return Ret.OK

    def finish(self):
        """
        Finish the conversion process.
        """
        # Single document mode?
        if self._args.single_document is True:
            assert self._document is not None
            self._print_test_case_results()

        return super().finish()

    def _get_table_row(self, test_case_result: Record_Object) -> list[str]:
        """Get the table row for the given test case.

        Args:
            test_case_result (Record_Object): Test case result.

        Returns:
            list[str]: Table row
        """
        test_case_result_attributes = test_case_result.to_python_dict()

        test_function_name = self._get_attribute(test_case_result, "name")
        test_result = self._get_attribute(test_case_result, "result")

        test_case = test_case_result_attributes["relates"]
        if test_case is None:
            test_case = RstText.escape("N/A")
        elif isinstance(test_case, list):
            test_case_links = []
            for tc in test_case:
                anchor_tag = tc.replace("SwTests.", TEST_CASES_FILE_NAME + "-").lower()
                test_case_links.append(RstText.link(tc, anchor_tag))

            test_case = ", ".join(test_case_links)
        else:
            anchor_tag = test_case.replace("SwTests.", TEST_CASES_FILE_NAME + "-").lower()

            test_case = RstText.link(test_case, anchor_tag)

        test_function_name = self._get_anchor(test_case_result) + RstText.escape(test_function_name)

        if test_result == "PASSED":
            test_result = RstText.role(test_result, "green")
        elif test_result == "FAILED":
            test_result = RstText.role(test_result, "red")

        row = [test_case, test_function_name, test_result]

        return row

    def _get_anchor(self, test_case_result: Record_Object) -> str:
        """Get the anchor of the given test case result as inline raw HTML.

        The anchor ID follows the label scheme of the converted records: the reStructuredText
        file name, a hyphen and the lowercase record name, e.g.
        "sw_test_result_report.rst-test_cli_result". It allows links to the row of a result.

        Args:
            test_case_result (Record_Object): Test case result.

        Returns:
            str: Anchor as raw-html role
        """
        file_name = self._file_name_trlc_to_rst(test_case_result.location.file_name)
        anchor_id = f"{file_name}-{test_case_result.name.lower().replace(' ', '-')}"

        # The escaped space ends the role without adding a space to the cell text.
        return f":raw-html:`<span id=\"{anchor_id}\"></span>`\\ "

    def _print_test_case_results(self) -> None:
        """Prints the software test case results.
        """
        assert self._document is not None

        column_titles = ["Test Case", "Test Function", "Test Result"]

        rows = [self._get_table_row(test_case_result) for test_case_result in self._test_case_results]

        self._document.add(RstRawText(RAW_HTML_ROLE))
        self._document.add(RstTable(column_titles, rows))

# Functions ********************************************************************

# Main *************************************************************************
