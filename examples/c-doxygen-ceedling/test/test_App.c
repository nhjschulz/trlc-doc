/* BSD 3-Clause License
 *
 * Copyright (c) 2025, NewTec GmbH
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its
 *    contributors may be used to endorse or promote products derived from
 *    this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/*******************************************************************************
    DESCRIPTION
*******************************************************************************/
/**
 * @file   test_App.c
 * @brief  Tests for App
 * @author Andreas Merkle <web@blue-andi.de>
 */

/******************************************************************************
 * Includes
 *****************************************************************************/

#include "unity.h"
#include <stdlib.h>
#include <getopt.h>
#include <string.h>
#include "App.h"

#include "Lobster.h"
#include "mock_Greeter.h"
#include "stub_Printer.h"

/******************************************************************************
 * Compiler Switches
 *****************************************************************************/

/******************************************************************************
 * Macros
 *****************************************************************************/

/**
 * A macro to calculate the number of elements in an array.
 * This macro is used to determine the size of an array at compile time.
 * It divides the total size of the array by the size of a single element.
 *
 * @param _array The array for which the number of elements is to be calculated.
 */
#define ARRAY_NUM_ELEMENTS(_array) (sizeof(_array) / sizeof((_array)[0]))

/******************************************************************************
 * Types and classes
 *****************************************************************************/

/******************************************************************************
 * Prototypes
 *****************************************************************************/

/******************************************************************************
 * Local Variables
 *****************************************************************************/

/**
 * @brief Buffer used to capture stdout.
 */
static char gCaptureBufferStdout[512U];

/**
 * @brief Buffer used to capture stderr.
 */
static char gCaptureBufferStderr[512U];

/**
 * @brief Hour threshold for morning.
 */
static const int HOUR_THRESHOLD_MORNING   = 5;

/**
 * @brief Hour threshold for midday.
 */
static const int HOUR_THRESHOLD_MIDDAY    = 11;

/**
 * @brief Hour threshold for afternoon.
 */
static const int HOUR_THRESHOLD_AFTERNOON = 13;

/**
 * @brief Hour threshold for night.
 */
static const int HOUR_THRESHOLD_NIGHT     = 19;

/******************************************************************************
 * Public Methods
 *****************************************************************************/

/******************************************************************************
 * Protected Methods
 *****************************************************************************/

/******************************************************************************
 * Private Methods
 *****************************************************************************/

/******************************************************************************
 * External Functions
 *****************************************************************************/

/**
 * @brief Set up the test environment.
 * This function is called before each test case to set up the necessary environment.
 * 
 * @justification{Test framework specific function to setup a test case.}
 */
void setUp(void)
{
    Printer_testInit(gCaptureBufferStdout, sizeof(gCaptureBufferStdout), gCaptureBufferStderr, sizeof(gCaptureBufferStderr));
}

/**
 * @brief Tear down the test environment.
 * This function is called after each test case to clean up the environment.
 * 
 * @justification{Test framework specific function to tear down a test case.}
 */
void tearDown(void)
{
    Printer_testClearBufferStdout();
    Printer_testClearBufferStderr();
}

/**
 * @brief Test CLI.
 * Test the command-line interface (CLI) argument handling of the `main` function.
 * This test simulates passing a command-line argument to the program and verifies
 * that the `main` function executes successfully with the provided input.
 *
 * @implements{SwTests.tc_cli}
 */
void test_App_cli(void)
{
    const char* userName = "Alice";
    const char* argv[]   = { "greet", userName };

    LOBSTER_TRACE("SwTests.tc_cli");

    optind = 0; /* Reset optind to ensure getopt_long starts fresh. */
    Greeter_init_Expect(HOUR_THRESHOLD_MORNING, HOUR_THRESHOLD_MIDDAY, HOUR_THRESHOLD_AFTERNOON, HOUR_THRESHOLD_NIGHT);
    Greeter_greet_Expect(userName);

    TEST_ASSERT_EQUAL_INT(0, App_run(ARRAY_NUM_ELEMENTS(argv), (char**)&argv));
}

/**
 * @brief Test CLI help message.
 * Test the command-line interface (CLI) help message of the `main` function.
 *
 * @implements{SwTests.tc_cli_usage_help}
 * @implements{SwTests.tc_cli_stdout}
 */
void test_App_usageHelp(void)
{
    const char* argv[] = { "greet", "-h" };
    const char* expectedStdoutOutput =
        "A C CLI tool to greet a user considering the time.\n"
        "Usage: greet <option(s)> [NAME]\n"
        "\tArguments:\n"
        "\t\tNAME\t\tSpecify a user name to greet, defaults to login name if unset.\n"
        "\tOptions:\n"
        "\t\t--help, -h\tShow this help message.\n"
        "\n"
        "Copyright (c) 2025 NewTec GmbH\n";

    LOBSTER_TRACE("SwTests.tc_cli_usage_help");

    optind = 0; /* Reset optind to ensure getopt_long starts fresh. */
    Greeter_init_Ignore();
    Greeter_greet_Ignore();

    TEST_ASSERT_EQUAL_INT(-1, App_run(ARRAY_NUM_ELEMENTS(argv), (char**)&argv));
    TEST_ASSERT_EQUAL_STRING_LEN(expectedStdoutOutput, gCaptureBufferStdout, strlen(expectedStdoutOutput));
}

/**
 * @brief Test usage error.
 * Test the command-line interface (CLI) error handling of the `main` function.
 *
 * @implements{SwTests.tc_cli_usage_error}
 */
void test_App_usageError(void)
{
    const char* argv[] = { "greet", "--unknown" };
    const char* expectedStderrOutput = "Error: Unknown option: --unknown";

    LOBSTER_TRACE("SwTests.tc_cli_usage_error");

    optind = 0; /* Reset optind to ensure getopt_long starts fresh. */
    Greeter_init_Ignore();
    Greeter_greet_Ignore();

    TEST_ASSERT_EQUAL_INT(-1, App_run(ARRAY_NUM_ELEMENTS(argv), (char**)&argv));
    TEST_ASSERT_EQUAL_STRING_LEN(expectedStderrOutput, gCaptureBufferStderr, strlen(expectedStderrOutput));
}

/******************************************************************************
 * Local Functions
 *****************************************************************************/
