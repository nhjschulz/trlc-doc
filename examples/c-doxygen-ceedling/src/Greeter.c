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
 * @file   Greeter.c
 * @brief  Greeter
 * @author Andreas Merkle <web@blue-andi.de>
 */

/******************************************************************************
 * Includes
 *****************************************************************************/
#include "Greeter.h"
#include <stdio.h>
#include <stdlib.h>
#include "LocalTime.h"
#include "Printer.h"

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

static const char* getUserName();
static int         getHourOfDay();

/******************************************************************************
 * Local Variables
 *****************************************************************************/

/** Hour threshold for morning. */
static int gHourThresholdMorning   = 0;

/** Hour threshold for midday. */
static int gHourThresholdMidday    = 0;

/** Hour threshold for afternoon. */
static int gHourThresholdAfternoon = 0;

/** Hour threshold for night. */
static int gHourThresholdNight     = 0;

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

void Greeter_init(int hourThresholdMorning, int hourThresholdMidday, int hourThresholdAfternoon, int hourThresholdNight)
{
    gHourThresholdMorning   = hourThresholdMorning;
    gHourThresholdMidday    = hourThresholdMidday;
    gHourThresholdAfternoon = hourThresholdAfternoon;
    gHourThresholdNight     = hourThresholdNight;
}

void Greeter_greet(const char* userName)
{
    int         currentHour = getHourOfDay();
    const char* greeting    = NULL;

    if ((gHourThresholdMorning <= currentHour) && (currentHour < gHourThresholdMidday))
    {
        greeting = "Good morning";
    }
    else if ((gHourThresholdMidday <= currentHour) && (currentHour < gHourThresholdAfternoon))
    {
        greeting = "Good midday";
    }
    else if ((gHourThresholdAfternoon <= currentHour) && (currentHour < gHourThresholdNight))
    {
        greeting = "Good afternoon";
    }
    else
    {
        greeting = "Good night";
    }

    /* Check if a user name is given.
     * If not, use the login name of the user.
     */
    if ((NULL == userName) || ('\0' == userName[0]))
    {
        userName = getUserName();
    }

    Printer_printf("%s %s!", greeting, userName);
}

/******************************************************************************
 * Local Functions
 *****************************************************************************/

/**
 * @brief Get the user login name.
 *
 * @return User login name or nullptr if not available.
 *
 * @implements{SwRequirements.sw_req_cli_default_name}
 */
static const char* getUserName()
{
    const char* userName = getenv("USERNAME");

    if (NULL == userName)
    {
        userName = getenv("USER");
    }

    return userName;
}

/**
 * @brief Get the current hour of the day.
 *
 * @returns Current hour of the day.
 *
 * @implements{SwRequirements.sw_func_daytime_greeting_selection}
 */
static int getHourOfDay()
{
    int        hour      = 0;
    time_t     now       = LocalTime_time(NULL);
    struct tm* localTime = LocalTime_localtime(&now);

    if (NULL != localTime)
    {
        hour = localTime->tm_hour;
    }

    return hour;
}
