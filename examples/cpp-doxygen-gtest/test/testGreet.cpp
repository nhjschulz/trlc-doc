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
 * @file   testGreet.cpp
 * @brief  Test cases to test the greeting functionality.
 * @author Andreas Merkle <web@blue-andi.de>
 */

/******************************************************************************
 * Includes
 *****************************************************************************/
#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include <time.h>

/* A public domain header with a C/C++ macro to embed tracing tags or justifications.
 * See https://github.com/bmw-software-engineering/lobster/blob/main/support/gtest/include/lobster_gtest.h
 */
#include "lobster_gtest.h"

#include "App.h"
#include "Greeter.h"
#include "LocalTime.h"

#include "mocks/MockLocalTime.h"

using ::testing::Return, ::testing::EndsWith, ::testing::HasSubstr;

/**
 * @brief Annoymous namespace
 */
namespace
{

/******************************************************************************
 * Macros
 *****************************************************************************/

/******************************************************************************
 * Types and Classes
 *****************************************************************************/

/******************************************************************************
 * Prototypes
 *****************************************************************************/

/**
 * @brief Check if a value is within a specified range.
 *
 * @tparam T
 * @param[in] lo    The lower bound of the range.
 * @param[in] hi    The upper bound of the range.
 *
 * @return Return true if the value is within the range [lo, hi], otherwise false.
 * 
 * @justification{This function is a utility function used to check if a value is within a specified range, which is useful for testing time values.}
 */
template <typename T>
static auto isInRange(T lo, T hi)
{
    return testing::AllOf(testing::Ge((lo)), testing::Le((hi)));
}

/******************************************************************************
 * Variables
 *****************************************************************************/

/******************************************************************************
 * External functions
 *****************************************************************************/

/**
 * @brief Test night time greeting.
 * This test verifies that the greet function returns "Good night <name>!"
 * when the time is between 19:00 and 04:59.
 *
 * @implements{SwTests.tc_greet_night_time_greeting}
 */
TEST(TSGreet, NightTimeGreeting)
{
    MockLocalTime localTime;
    Greeter       greeter(
        localTime,
        App::HOUR_THRESHOLD_MORNING,
        App::HOUR_THRESHOLD_MIDDAY,
        App::HOUR_THRESHOLD_AFTERNOON,
        App::HOUR_THRESHOLD_NIGHT);
    int mockHour;
    int mockMinute;

    LOBSTER_TRACE("SwTests.tc_greet_night_time_greeting");

    for (mockHour = App::HOUR_THRESHOLD_NIGHT; mockHour < (24 + App::HOUR_THRESHOLD_MORNING); ++mockHour)
    {
        for (mockMinute = 0; mockMinute < 60; ++mockMinute)
        {
            tm localTimeResult;

            localTimeResult.tm_hour = mockHour % 24;
            localTimeResult.tm_min  = mockMinute;

            EXPECT_CALL(localTime, time(nullptr)).Times(1);
            EXPECT_CALL(localTime, localtime).Times(1).WillOnce(Return(&localTimeResult));

            ASSERT_STREQ(greeter.greet("Alice").c_str(), "Good night Alice!");
        }
    }
}

/**
 * @brief Test morning time greeting.
 * This test verifies that the greet function returns "Good morning <name>!"
 * when the time is between 05:00 and 10:59.
 *
 * @implements{SwTests.tc_greet_morning_time_greeting}
 */
TEST(TSGreet, MorningTimeGreeting)
{
    MockLocalTime localTime;
    Greeter       greeter(
        localTime,
        App::HOUR_THRESHOLD_MORNING,
        App::HOUR_THRESHOLD_MIDDAY,
        App::HOUR_THRESHOLD_AFTERNOON,
        App::HOUR_THRESHOLD_NIGHT);
    int mockHour;
    int mockMinute;

    LOBSTER_TRACE("SwTests.tc_greet_morning_time_greeting");

    for (mockHour = App::HOUR_THRESHOLD_MORNING; mockHour < App::HOUR_THRESHOLD_MIDDAY; ++mockHour)
    {
        for (mockMinute = 0; mockMinute < 60; ++mockMinute)
        {
            tm localTimeResult;

            localTimeResult.tm_hour = mockHour;
            localTimeResult.tm_min  = mockMinute;

            EXPECT_CALL(localTime, time(nullptr)).Times(1);
            EXPECT_CALL(localTime, localtime).Times(1).WillOnce(Return(&localTimeResult));

            ASSERT_STREQ(greeter.greet("Bob").c_str(), "Good morning Bob!");
        }
    }
}

/**
 * @brief Test midday time greeting.
 * This test verifies that the greet function returns "Good midday <name>!"
 * when the time is between 11:00 and 12:59.
 *
 * @implements{SwTests.tc_greet_midday_time_greeting}
 */
TEST(TSGreet, MiddayTimeGreeting)
{
    MockLocalTime localTime;
    Greeter       greeter(
        localTime,
        App::HOUR_THRESHOLD_MORNING,
        App::HOUR_THRESHOLD_MIDDAY,
        App::HOUR_THRESHOLD_AFTERNOON,
        App::HOUR_THRESHOLD_NIGHT);
    int mockHour;
    int mockMinute;

    LOBSTER_TRACE("SwTests.tc_greet_midday_time_greeting");

    for (mockHour = App::HOUR_THRESHOLD_MIDDAY; mockHour < App::HOUR_THRESHOLD_AFTERNOON; ++mockHour)
    {
        for (mockMinute = 0; mockMinute < 60; ++mockMinute)
        {
            tm localTimeResult;

            localTimeResult.tm_hour = mockHour;
            localTimeResult.tm_min  = mockMinute;

            EXPECT_CALL(localTime, time(nullptr)).Times(1);
            EXPECT_CALL(localTime, localtime).Times(1).WillOnce(Return(&localTimeResult));

            ASSERT_STREQ(greeter.greet("Charlize").c_str(), "Good midday Charlize!");
        }
    }
}

/**
 * @brief Test afterboon time greeting.
 * This test verifies that the greet function returns "Good afternoon <name>!"
 * when the time is between 13:00 and 18:59.
 *
 * @implements{SwTests.tc_greet_afternoon_time_greeting}
 */
TEST(TSGreet, AfternoonTimeGreeting)
{
    MockLocalTime localTime;
    Greeter       greeter(
        localTime,
        App::HOUR_THRESHOLD_MORNING,
        App::HOUR_THRESHOLD_MIDDAY,
        App::HOUR_THRESHOLD_AFTERNOON,
        App::HOUR_THRESHOLD_NIGHT);
    int mockHour;
    int mockMinute;

    LOBSTER_TRACE("SwTests.tc_greet_afternoon_time_greeting");

    for (mockHour = App::HOUR_THRESHOLD_AFTERNOON; mockHour < App::HOUR_THRESHOLD_NIGHT; ++mockHour)
    {
        for (mockMinute = 0; mockMinute < 60; ++mockMinute)
        {
            tm localTimeResult;

            localTimeResult.tm_hour = mockHour;
            localTimeResult.tm_min  = mockMinute;

            EXPECT_CALL(localTime, time(nullptr)).Times(1);
            EXPECT_CALL(localTime, localtime).Times(1).WillOnce(Return(&localTimeResult));

            ASSERT_STREQ(greeter.greet("Dominic").c_str(), "Good afternoon Dominic!");
        }
    }
}

/**
 * @brief Test greet with name provided.
 * This test verifies that the greet function returns the correct greeting
 * based on the provided name.
 *
 * @implements{SwTests.tc_greet_user_name}
 */
TEST(TSGreet, UserNameGreeting)
{
    MockLocalTime localTime;
    Greeter       greeter(
        localTime,
        App::HOUR_THRESHOLD_MORNING,
        App::HOUR_THRESHOLD_MIDDAY,
        App::HOUR_THRESHOLD_AFTERNOON,
        App::HOUR_THRESHOLD_NIGHT);

    LOBSTER_TRACE("SwTests.tc_greet_user_name");

    EXPECT_CALL(localTime, time(nullptr)).Times(1);
    EXPECT_CALL(localTime, localtime).Times(1);

    ASSERT_THAT(greeter.greet("Elton").c_str(), EndsWith("Elton!"));
}

/**
 * @brief Test greet without a name provided.
 * This test verifies that the greet function returns the login name in the
 * greeting when no name is provided.
 *
 * @implements{SwTests.tc_greet_default_name}
 */
TEST(TSGreet, DefaultNameGreeting)
{
    MockLocalTime localTime;
    Greeter       greeter(
        localTime,
        App::HOUR_THRESHOLD_MORNING,
        App::HOUR_THRESHOLD_MIDDAY,
        App::HOUR_THRESHOLD_AFTERNOON,
        App::HOUR_THRESHOLD_NIGHT);

    LOBSTER_TRACE("SwTests.tc_greet_default_name");

    EXPECT_CALL(localTime, time(nullptr)).Times(1);
    EXPECT_CALL(localTime, localtime).Times(1);

    /* Get the current user name. */
    const char* userName = getenv("USERNAME");
    if (nullptr == userName)
    {
        userName = getenv("USER");
    }

    ASSERT_THAT(greeter.greet(nullptr).c_str(), HasSubstr(userName));
}

/**
 * @brief Test local time functionality.
 * This test verifies that the LocalTime class correctly retrieves the current
 * local time and matches it with the system's local time.
 *
 * @implements{SwTests.tc_func_daytime_greeting_selection}
 */
TEST(TSGreet, LocalTime)
{
    LocalTime* testLocalTime = new LocalTime(); /* To get coverage for the destructor, create object on heap. */
    time_t     time1         = testLocalTime->time(nullptr);
    time_t     time2         = time(nullptr);
    struct tm* tm1           = testLocalTime->localtime(&time1);
    struct tm* tm2           = localtime(&time2);

    LOBSTER_TRACE("SwTests.tc_func_daytime_greeting_selection");

    ASSERT_EQ(time1, time2);
    ASSERT_EQ(tm1->tm_year, tm2->tm_year);
    ASSERT_EQ(tm1->tm_mon, tm2->tm_mon);
    ASSERT_EQ(tm1->tm_mday, tm2->tm_mday);
    ASSERT_EQ(tm1->tm_hour, tm2->tm_hour);
    ASSERT_EQ(tm1->tm_min, tm2->tm_min);
    ASSERT_THAT(tm1->tm_sec, isInRange(tm2->tm_sec, tm2->tm_sec + 1));

    delete testLocalTime;
}

/******************************************************************************
 * Local functions
 *****************************************************************************/

} /* namespace */
