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
 * @file   testCmdLine.cpp
 * @brief  Test for command line argument handling
 * @author Andreas Merkle <web@blue-andi.de>
 */

/******************************************************************************
 * Includes
 *****************************************************************************/
#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include <getopt.h>

/* A public domain header with a C/C++ macro to embed tracing tags or justifications.
 * See https://github.com/bmw-software-engineering/lobster/blob/main/support/gtest/include/lobster_gtest.h
 */
#include "lobster_gtest.h"

#include "App.h"

using ::testing::HasSubstr;

/**
 * @brief Annoymous namespace
 */
namespace
{

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
 * Types and Classes
 *****************************************************************************/

/******************************************************************************
 * Prototypes
 *****************************************************************************/

/******************************************************************************
 * Variables
 *****************************************************************************/

/******************************************************************************
 * External functions
 *****************************************************************************/

/**
 * @brief Test CLI.
 * Test the command-line interface (CLI) argument handling of the `main` function.
 * This test simulates passing a command-line argument to the program and verifies
 * that the `main` function executes successfully with the provided input.
 *
 * @implements{SwTests.tc_cli}
 */
TEST(TSCmdLine, Cli)
{
    App         app;
    const char* argv[] = { "greet", "Alice" };

    LOBSTER_TRACE("SwTests.tc_cli");

    testing::internal::CaptureStdout();
    optind = 0; /* Reset optind to ensure getopt_long starts fresh. */
    ASSERT_EQ(0, app.run(ARRAY_NUM_ELEMENTS(argv), (char**)&argv));
    testing::internal::GetCapturedStdout();
}

/**
 * @brief Test stdout.
 * Test the command-line interface (CLI) output of the `main` function.
 *
 * @implements{SwTests.tc_cli_stdout}
 */
TEST(TSCmdLine, Stdout)
{
    App         app;
    const char* argv[] = { "greet", "Tom" };

    LOBSTER_TRACE("SwTests.tc_cli_stdout");

    testing::internal::CaptureStdout();
    optind = 0; /* Reset optind to ensure getopt_long starts fresh. */
    app.run(ARRAY_NUM_ELEMENTS(argv), (char**)&argv);
    std::string output = testing::internal::GetCapturedStdout();

    ASSERT_THAT(output, HasSubstr("Tom!"));
}

/**
 * @brief Test CLI help message.
 * Test the command-line interface (CLI) help message of the `main` function.
 *
 * @implements{SwTests.tc_cli_usage_help}
 */
TEST(TSCmdLine, UsageHelp)
{
    App         app;
    const char* argv[] = { "greet", "-h" };

    LOBSTER_TRACE("SwTests.tc_cli_usage_help");

    testing::internal::CaptureStdout();
    optind = 0; /* Reset optind to ensure getopt_long starts fresh. */
    app.run(ARRAY_NUM_ELEMENTS(argv), (char**)&argv);
    std::string output = testing::internal::GetCapturedStdout();

    ASSERT_THAT(output, HasSubstr("Usage: greet <option(s)> [NAME]"));
    ASSERT_THAT(output, HasSubstr("Specify a user name to greet, defaults to login name if unset."));
    ASSERT_THAT(output, HasSubstr("--help, -h\tShow this help message."));
    ASSERT_THAT(output, HasSubstr("Copyright (c) 2025 NewTec GmbH"));
}

/**
 * @brief Test usage error.
 * Test the command-line interface (CLI) error handling of the `main` function.
 *
 * @implements{SwTests.tc_cli_usage_error}
 */
TEST(TSCmdLine, UsageError)
{
    App         app;
    const char* argv[] = { "greet", "--unknown" };

    LOBSTER_TRACE("SwTests.tc_cli_usage_error");

    testing::internal::CaptureStdout();
    testing::internal::CaptureStderr();
    optind = 0; /* Reset optind to ensure getopt_long starts fresh. */
    app.run(ARRAY_NUM_ELEMENTS(argv), (char**)&argv);
    std::string errOutput = testing::internal::GetCapturedStderr();
    (void)testing::internal::GetCapturedStdout();

    ASSERT_THAT(errOutput, HasSubstr("Error: Unknown option: --unknown"));
}

/******************************************************************************
 * Local functions
 *****************************************************************************/

} /* namespace */
