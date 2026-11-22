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
 * @file   test_Greeter.c
 * @brief  Tests for Greeter
 * @author Andreas Merkle <web@blue-andi.de>
 */

/******************************************************************************
 * Includes
 *****************************************************************************/

#include "unity.h"
#include <stdlib.h>
#include <string.h>
#include "Greeter.h"

#include "Lobster.h"
#include "mock_LocalTime.h"
#include "stub_Printer.h"

/******************************************************************************
 * Compiler Switches
 *****************************************************************************/

/******************************************************************************
 * Macros
 *****************************************************************************/

/******************************************************************************
 * Types and classes
 *****************************************************************************/

/******************************************************************************
 * Prototypes
 *****************************************************************************/

static time_t getMockTime(int year, int month, int day, int hour, int minute);

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

/**
 * @brief The mock time year used for testing.
 * This is used to ensure that the year is consistent across tests.
 */
static const int YEAR                     = 2021;

/**
 * @brief The mock time month used for testing.
 * This is used to ensure that the month is consistent across tests.
 */
static const int MONTH                    = 1;

/**
 * @brief The mock time day used for testing.
 * This is used to ensure that the day is consistent across tests.
 */
static const int DAY                      = 1;

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

    Greeter_init(
        HOUR_THRESHOLD_MORNING,
        HOUR_THRESHOLD_MIDDAY,
        HOUR_THRESHOLD_AFTERNOON,
        HOUR_THRESHOLD_NIGHT);
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
 * @brief Test morning greeting equivalence class 0 (EC0).
 *
 * @implements{SwTests.tc_greet_morning_time_greeting}
 * @implements{SwTests.tc_greet_user_name}
 * @implements{SwTests.tc_cli_stdout}
 * @implements{SwTests.tc_func_daytime_greeting_selection}
 */
void test_Greeter_morningGreetingEC0(void)
{
    int mockHoursEC0[] = {
        HOUR_THRESHOLD_MORNING,
        HOUR_THRESHOLD_MIDDAY - 1
    };
    int mockMinutesEC0[] = {
        0,
        59
    };
    time_t mockTimesEC0[] = {
        getMockTime(YEAR, MONTH, DAY, mockHoursEC0[0U], mockMinutesEC0[0U]),
        getMockTime(YEAR, MONTH, DAY, mockHoursEC0[1U], mockMinutesEC0[1U])
    };
    const char* expectedGreeting       = "Good morning Bob!";
    size_t      expectedGreetingLength = strlen(expectedGreeting);
    size_t      idx;

    LOBSTER_TRACE("SwTests.tc_greet_morning_time_greeting");
    LOBSTER_TRACE("SwTests.tc_greet_user_name");
    LOBSTER_TRACE("SwTests.tc_cli_stdout");
    LOBSTER_TRACE("SwTests.tc_func_daytime_greeting_selection");

    for (idx = 0U; idx < sizeof(mockTimesEC0) / sizeof(mockTimesEC0[0]); ++idx)
    {
        time_t    mockTime        = mockTimesEC0[idx];
        struct tm localTimeResult = { 0 };

        localTimeResult.tm_year   = YEAR - 1900;
        localTimeResult.tm_mon    = MONTH - 1;
        localTimeResult.tm_mday   = DAY;
        localTimeResult.tm_hour   = mockHoursEC0[idx];
        localTimeResult.tm_min    = mockMinutesEC0[idx];

        LocalTime_time_ExpectAndReturn(NULL, mockTime);
        LocalTime_localtime_ExpectAndReturn(&mockTime, &localTimeResult);

        Greeter_greet("Bob");

        /* Check the greeting message. */
        TEST_ASSERT_EQUAL_STRING_LEN(expectedGreeting, gCaptureBufferStdout, expectedGreetingLength);
    }
}

/**
 * @brief Test morning greeting equivalence class 1 (EC1).
 *
 * @implements{SwTests.tc_greet_morning_time_greeting}
 * @implements{SwTests.tc_greet_user_name}
 * @implements{SwTests.tc_cli_stdout}
 * @implements{SwTests.tc_func_daytime_greeting_selection}
 */
void test_Greeter_morningGreetingEC1(void)
{
    int mockHoursEC1[] = {
        HOUR_THRESHOLD_MORNING - 1,
        HOUR_THRESHOLD_MIDDAY
    };
    int mockMinutesEC1[] = {
        59,
        0
    };
    time_t mockTimesEC1[] = {
        getMockTime(YEAR, MONTH, DAY, mockHoursEC1[0U], mockMinutesEC1[0U]),
        getMockTime(YEAR, MONTH, DAY, mockHoursEC1[1U], mockMinutesEC1[1U])
    };
    const char* expectedGreeting       = "Good morning Alice!";
    size_t      expectedGreetingLength = strlen(expectedGreeting);
    size_t      idx;

    LOBSTER_TRACE("SwTests.tc_greet_morning_time_greeting");
    LOBSTER_TRACE("SwTests.tc_greet_user_name");
    LOBSTER_TRACE("SwTests.tc_cli_stdout");
    LOBSTER_TRACE("SwTests.tc_func_daytime_greeting_selection");

    for (idx = 0U; idx < sizeof(mockTimesEC1) / sizeof(mockTimesEC1[0]); ++idx)
    {
        time_t    mockTime        = mockTimesEC1[idx];
        struct tm localTimeResult = { 0 };

        localTimeResult.tm_year   = YEAR - 1900;
        localTimeResult.tm_mon    = MONTH - 1;
        localTimeResult.tm_mday   = DAY;
        localTimeResult.tm_hour   = mockHoursEC1[idx];
        localTimeResult.tm_min    = mockMinutesEC1[idx];

        LocalTime_time_ExpectAndReturn(NULL, mockTime);
        LocalTime_localtime_ExpectAndReturn(&mockTime, &localTimeResult);

        Greeter_greet("Alice");

        /* Check the greeting message. */
        TEST_ASSERT(0 != strncmp(expectedGreeting, gCaptureBufferStdout, expectedGreetingLength));
    }
}

/**
 * @brief Test midday greeting equivalence class 0 (EC0).
 *
 * @implements{SwTests.tc_greet_midday_time_greeting}
 * @implements{SwTests.tc_greet_user_name}
 * @implements{SwTests.tc_cli_stdout}
 * @implements{SwTests.tc_func_daytime_greeting_selection}
 */
void test_Greeter_middayGreetingEC0(void)
{
    int mockHoursEC0[] = {
        HOUR_THRESHOLD_MIDDAY,
        HOUR_THRESHOLD_AFTERNOON - 1
    };
    int mockMinutesEC0[] = {
        0,
        59
    };
    time_t mockTimesEC0[] = {
        getMockTime(YEAR, MONTH, DAY, mockHoursEC0[0U], mockMinutesEC0[0U]),
        getMockTime(YEAR, MONTH, DAY, mockHoursEC0[1U], mockMinutesEC0[1U])
    };
    const char* expectedGreeting       = "Good midday Charlie!";
    size_t      expectedGreetingLength = strlen(expectedGreeting);
    size_t      idx;

    LOBSTER_TRACE("SwTests.tc_greet_midday_time_greeting");
    LOBSTER_TRACE("SwTests.tc_greet_user_name");
    LOBSTER_TRACE("SwTests.tc_cli_stdout");
    LOBSTER_TRACE("SwTests.tc_func_daytime_greeting_selection");

    for (idx = 0U; idx < sizeof(mockTimesEC0) / sizeof(mockTimesEC0[0]); ++idx)
    {
        time_t    mockTime        = mockTimesEC0[idx];
        struct tm localTimeResult = { 0 };

        localTimeResult.tm_year   = YEAR - 1900;
        localTimeResult.tm_mon    = MONTH - 1;
        localTimeResult.tm_mday   = DAY;
        localTimeResult.tm_hour   = mockHoursEC0[idx];
        localTimeResult.tm_min    = mockMinutesEC0[idx];

        LocalTime_time_ExpectAndReturn(NULL, mockTime);
        LocalTime_localtime_ExpectAndReturn(&mockTime, &localTimeResult);

        Greeter_greet("Charlie");

        /* Check the greeting message. */
        TEST_ASSERT_EQUAL_STRING_LEN(expectedGreeting, gCaptureBufferStdout, expectedGreetingLength);
    }
}

/**
 * @brief Test midday greeting equivalence class 1 (EC1).
 *
 * @implements{SwTests.tc_greet_midday_time_greeting}
 * @implements{SwTests.tc_greet_user_name}
 * @implements{SwTests.tc_cli_stdout}
 * @implements{SwTests.tc_func_daytime_greeting_selection}
 */
void test_Greeter_middayGreetingEC1(void)
{
    int mockHoursEC1[] = {
        HOUR_THRESHOLD_MIDDAY - 1,
        HOUR_THRESHOLD_AFTERNOON
    };
    int mockMinutesEC1[] = {
        59,
        0
    };
    time_t mockTimesEC1[] = {
        getMockTime(YEAR, MONTH, DAY, mockHoursEC1[0U], mockMinutesEC1[0U]),
        getMockTime(YEAR, MONTH, DAY, mockHoursEC1[1U], mockMinutesEC1[1U])
    };
    const char* expectedGreeting       = "Good midday Dave!";
    size_t      expectedGreetingLength = strlen(expectedGreeting);
    size_t      idx;

    LOBSTER_TRACE("SwTests.tc_greet_midday_time_greeting");
    LOBSTER_TRACE("SwTests.tc_greet_user_name");
    LOBSTER_TRACE("SwTests.tc_cli_stdout");
    LOBSTER_TRACE("SwTests.tc_func_daytime_greeting_selection");

    for (idx = 0U; idx < sizeof(mockTimesEC1) / sizeof(mockTimesEC1[0]); ++idx)
    {
        time_t    mockTime        = mockTimesEC1[idx];
        struct tm localTimeResult = { 0 };

        localTimeResult.tm_year   = YEAR - 1900;
        localTimeResult.tm_mon    = MONTH - 1;
        localTimeResult.tm_mday   = DAY;
        localTimeResult.tm_hour   = mockHoursEC1[idx];
        localTimeResult.tm_min    = mockMinutesEC1[idx];

        LocalTime_time_ExpectAndReturn(NULL, mockTime);
        LocalTime_localtime_ExpectAndReturn(&mockTime, &localTimeResult);

        Greeter_greet("Dave");

        /* Check the greeting message. */
        TEST_ASSERT(0 != strncmp(expectedGreeting, gCaptureBufferStdout, expectedGreetingLength));
    }
}

/**
 * @brief Test afternoon greeting equivalence class 0 (EC0).
 *
 * @implements{SwTests.tc_greet_afternoon_time_greeting}
 * @implements{SwTests.tc_greet_user_name}
 * @implements{SwTests.tc_cli_stdout}
 * @implements{SwTests.tc_func_daytime_greeting_selection}
 */
void test_Greeter_afternoonGreetingEC0(void)
{
    int mockHoursEC0[] = {
        HOUR_THRESHOLD_AFTERNOON,
        HOUR_THRESHOLD_NIGHT - 1
    };
    int mockMinutesEC0[] = {
        0,
        59
    };
    time_t mockTimesEC0[] = {
        getMockTime(YEAR, MONTH, DAY, mockHoursEC0[0U], mockMinutesEC0[0U]),
        getMockTime(YEAR, MONTH, DAY, mockHoursEC0[1U], mockMinutesEC0[1U])
    };
    const char* expectedGreeting       = "Good afternoon Eve!";
    size_t      expectedGreetingLength = strlen(expectedGreeting);
    size_t      idx;

    LOBSTER_TRACE("SwTests.tc_greet_afternoon_time_greeting");
    LOBSTER_TRACE("SwTests.tc_greet_user_name");
    LOBSTER_TRACE("SwTests.tc_cli_stdout");
    LOBSTER_TRACE("SwTests.tc_func_daytime_greeting_selection");

    for (idx = 0U; idx < sizeof(mockTimesEC0) / sizeof(mockTimesEC0[0]); ++idx)
    {
        time_t    mockTime        = mockTimesEC0[idx];
        struct tm localTimeResult = { 0 };

        localTimeResult.tm_year   = YEAR - 1900;
        localTimeResult.tm_mon    = MONTH - 1;
        localTimeResult.tm_mday   = DAY;
        localTimeResult.tm_hour   = mockHoursEC0[idx];
        localTimeResult.tm_min    = mockMinutesEC0[idx];

        LocalTime_time_ExpectAndReturn(NULL, mockTime);
        LocalTime_localtime_ExpectAndReturn(&mockTime, &localTimeResult);

        Greeter_greet("Eve");

        /* Check the greeting message. */
        TEST_ASSERT_EQUAL_STRING_LEN(expectedGreeting, gCaptureBufferStdout, expectedGreetingLength);
    }
}

/**
 * @brief Test afternoon greeting equivalence class 1 (EC1).
 *
 * @implements{SwTests.tc_greet_afternoon_time_greeting}
 * @implements{SwTests.tc_greet_user_name}
 * @implements{SwTests.tc_cli_stdout}
 * @implements{SwTests.tc_func_daytime_greeting_selection}
 */
void test_Greeter_afternoonGreetingEC1(void)
{
    int mockHoursEC1[] = {
        HOUR_THRESHOLD_AFTERNOON - 1,
        HOUR_THRESHOLD_NIGHT
    };
    int mockMinutesEC1[] = {
        59,
        0
    };
    time_t mockTimesEC1[] = {
        getMockTime(YEAR, MONTH, DAY, mockHoursEC1[0U], mockMinutesEC1[0U]),
        getMockTime(YEAR, MONTH, DAY, mockHoursEC1[1U], mockMinutesEC1[1U])
    };
    const char* expectedGreeting       = "Good afternoon Frank!";
    size_t      expectedGreetingLength = strlen(expectedGreeting);
    size_t      idx;

    LOBSTER_TRACE("SwTests.tc_greet_afternoon_time_greeting");
    LOBSTER_TRACE("SwTests.tc_greet_user_name");
    LOBSTER_TRACE("SwTests.tc_cli_stdout");
    LOBSTER_TRACE("SwTests.tc_func_daytime_greeting_selection");

    for (idx = 0U; idx < sizeof(mockTimesEC1) / sizeof(mockTimesEC1[0]); ++idx)
    {
        time_t    mockTime        = mockTimesEC1[idx];
        struct tm localTimeResult = { 0 };

        localTimeResult.tm_year   = YEAR - 1900;
        localTimeResult.tm_mon    = MONTH - 1;
        localTimeResult.tm_mday   = DAY;
        localTimeResult.tm_hour   = mockHoursEC1[idx];
        localTimeResult.tm_min    = mockMinutesEC1[idx];

        LocalTime_time_ExpectAndReturn(NULL, mockTime);
        LocalTime_localtime_ExpectAndReturn(&mockTime, &localTimeResult);

        Greeter_greet("Frank");

        /* Check the greeting message. */
        TEST_ASSERT(0 != strncmp(expectedGreeting, gCaptureBufferStdout, expectedGreetingLength));
    }
}

/**
 * @brief Test night greeting equivalence class 0 (EC0).
 *
 * @implements{SwTests.tc_greet_night_time_greeting}
 * @implements{SwTests.tc_greet_user_name}
 * @implements{SwTests.tc_cli_stdout}
 * @implements{SwTests.tc_func_daytime_greeting_selection}
 */
void test_Greeter_nightGreetingEC0(void)
{
    int mockHoursEC0[] = {
        HOUR_THRESHOLD_NIGHT,
        HOUR_THRESHOLD_MORNING - 1
    };
    int mockMinutesEC0[] = {
        0,
        59
    };
    time_t mockTimesEC0[] = {
        getMockTime(YEAR, MONTH, DAY, mockHoursEC0[0U], mockMinutesEC0[0U]),
        getMockTime(YEAR, MONTH, DAY, mockHoursEC0[1U], mockMinutesEC0[1U])
    };
    const char* expectedGreeting       = "Good night Grace!";
    size_t      expectedGreetingLength = strlen(expectedGreeting);
    size_t      idx;

    LOBSTER_TRACE("SwTests.tc_greet_night_time_greeting");
    LOBSTER_TRACE("SwTests.tc_greet_user_name");
    LOBSTER_TRACE("SwTests.tc_cli_stdout");
    LOBSTER_TRACE("SwTests.tc_func_daytime_greeting_selection");

    for (idx = 0U; idx < sizeof(mockTimesEC0) / sizeof(mockTimesEC0[0]); ++idx)
    {
        time_t    mockTime        = mockTimesEC0[idx];
        struct tm localTimeResult = { 0 };

        localTimeResult.tm_year   = YEAR - 1900;
        localTimeResult.tm_mon    = MONTH - 1;
        localTimeResult.tm_mday   = DAY;
        localTimeResult.tm_hour   = mockHoursEC0[idx];
        localTimeResult.tm_min    = mockMinutesEC0[idx];

        LocalTime_time_ExpectAndReturn(NULL, mockTime);
        LocalTime_localtime_ExpectAndReturn(&mockTime, &localTimeResult);

        Greeter_greet("Grace");

        /* Check the greeting message. */
        TEST_ASSERT_EQUAL_STRING_LEN(expectedGreeting, gCaptureBufferStdout, expectedGreetingLength);
    }
}

/**
 * @brief Test night greeting equivalence class 1 (EC1).
 *
 * @implements{SwTests.tc_greet_night_time_greeting}
 * @implements{SwTests.tc_greet_user_name}
 * @implements{SwTests.tc_cli_stdout}
 * @implements{SwTests.tc_func_daytime_greeting_selection}
 */
void test_Greeter_nightGreetingEC1(void)
{
    int mockHoursEC1[] = {
        HOUR_THRESHOLD_NIGHT - 1,
        HOUR_THRESHOLD_MORNING
    };
    int mockMinutesEC1[] = {
        59,
        0
    };
    time_t mockTimesEC1[] = {
        getMockTime(YEAR, MONTH, DAY, mockHoursEC1[0U], mockMinutesEC1[0U]),
        getMockTime(YEAR, MONTH, DAY, mockHoursEC1[1U], mockMinutesEC1[1U])
    };
    const char* expectedGreeting       = "Good night Hannah!";
    size_t      expectedGreetingLength = strlen(expectedGreeting);
    size_t      idx;

    LOBSTER_TRACE("SwTests.tc_greet_night_time_greeting");
    LOBSTER_TRACE("SwTests.tc_greet_user_name");
    LOBSTER_TRACE("SwTests.tc_cli_stdout");
    LOBSTER_TRACE("SwTests.tc_func_daytime_greeting_selection");

    for (idx = 0U; idx < sizeof(mockTimesEC1) / sizeof(mockTimesEC1[0]); ++idx)
    {
        time_t    mockTime        = mockTimesEC1[idx];
        struct tm localTimeResult = { 0 };

        localTimeResult.tm_year   = YEAR - 1900;
        localTimeResult.tm_mon    = MONTH - 1;
        localTimeResult.tm_mday   = DAY;
        localTimeResult.tm_hour   = mockHoursEC1[idx];
        localTimeResult.tm_min    = mockMinutesEC1[idx];

        LocalTime_time_ExpectAndReturn(NULL, mockTime);
        LocalTime_localtime_ExpectAndReturn(&mockTime, &localTimeResult);

        Greeter_greet("Hannah");

        /* Check the greeting message. */
        TEST_ASSERT(0 != strncmp(expectedGreeting, gCaptureBufferStdout, expectedGreetingLength));
    }
}

/**
 * @brief Test greet without a name provided.
 * This test verifies that the greet function returns the login name in the
 * greeting when no name is provided.
 *
 * @implements{SwTests.tc_greet_default_name}
 * @implements{SwTests.tc_cli_stdout}
 * @implements{SwTests.tc_func_daytime_greeting_selection}
 */
void test_Greeter_defaultNameGreeting(void)
{
    char        stdioBuffer[256U];
    time_t      mockTime        = getMockTime(YEAR, MONTH, DAY, HOUR_THRESHOLD_MORNING, 0);
    struct tm   localTimeResult = { 0 };
    const char* userName        = getenv("USERNAME");
    char        expectedGreeting[256U];

    if (NULL == userName)
    {
        userName = getenv("USER");

        if (NULL == userName)
        {
            /* Fallback if no environment variable is set. */
            userName = "User";
        }
    }

    LOBSTER_TRACE("SwTests.tc_greet_default_name");
    LOBSTER_TRACE("SwTests.tc_cli_stdout");
    LOBSTER_TRACE("SwTests.tc_func_daytime_greeting_selection");

    localTimeResult.tm_year = YEAR - 1900;
    localTimeResult.tm_mon  = MONTH - 1;
    localTimeResult.tm_mday = DAY;
    localTimeResult.tm_hour = HOUR_THRESHOLD_MORNING;
    localTimeResult.tm_min  = 0;

    LocalTime_time_ExpectAndReturn(NULL, mockTime);
    LocalTime_localtime_ExpectAndReturn(&mockTime, &localTimeResult);

    /* Prepare the expected greeting message. */
    snprintf(expectedGreeting, sizeof(expectedGreeting), "Good morning %s!", userName);

    Greeter_greet(NULL);

    TEST_ASSERT_EQUAL_STRING_LEN(expectedGreeting, gCaptureBufferStdout, strlen(expectedGreeting));
}

/******************************************************************************
 * Local Functions
 *****************************************************************************/

/**
 * @brief Get the mock time for testing.
 *
 * @param[in] year  The year (e.g., 2021).
 * @param[in] month The month (1-12).
 * @param[in] day   The day of the month (1-31).
 * @param[in] hour  The hour of the day (0-23).
 * @param[in] minute The minute of the hour (0-59).
 *
 * @return The mock time as a time_t value.
 * 
 * @justification{Utility function for testing purposes.}
 */
static time_t getMockTime(int year, int month, int day, int hour, int minute)
{
    /* Create a tm structure to represent the mock time. */
    struct tm mockTm = { 0 };

    mockTm.tm_year   = year - 1900; /* tm_year is years since 1900 */
    mockTm.tm_mon    = month - 1;   /* tm_mon is months since January */
    mockTm.tm_mday   = day;
    mockTm.tm_hour   = hour;
    mockTm.tm_min    = minute;
    mockTm.tm_sec    = 0;

    /* Convert the tm structure to time_t. */
    return mktime(&mockTm);
}
