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
 * @file   Greeter.cpp
 * @brief  Greeter class
 * @author Andreas Merkle <web@blue-andi.de>
 */

/******************************************************************************
 * Includes
 *****************************************************************************/
#include "Greeter.h"

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

/******************************************************************************
 * Local Variables
 *****************************************************************************/

/******************************************************************************
 * Public Methods
 *****************************************************************************/

std::string Greeter::greet(const char* userName)
{
    int             currentHour = getHourOfDay();
    std::string     greeting;

    if ((m_hourThresholdMorning <= currentHour) && (currentHour < m_hourThresholdMidday))
    {
        greeting = "Good morning ";
    }
    else if ((m_hourThresholdMidday <= currentHour) && (currentHour < m_hourThresholdAfternoon))
    {
        greeting = "Good midday ";
    }
    else if ((m_hourThresholdAfternoon <= currentHour) && (currentHour < m_hourThresholdNight))
    {
        greeting = "Good afternoon ";
    }
    else
    {
        greeting = "Good night ";
    }

    /* Check if a user name is given.
     * If not, use the login name of the user.
     */
    if ((nullptr == userName) || ('\0' == userName[0]))
    {
        userName = getUserName();
    }

    greeting += userName;
    greeting += "!";

    return greeting;
}

/******************************************************************************
 * Protected Methods
 *****************************************************************************/

/******************************************************************************
 * Private Methods
 *****************************************************************************/

const char* Greeter::getUserName() const
{
    const char* userName = getenv("USERNAME");

    if (nullptr == userName)
    {
        userName = getenv("USER");
    }

    return userName;
}

int Greeter::getHourOfDay() const
{
    int        hour      = 0;
    time_t     now       = m_localTime.time(nullptr);
    struct tm* localTime = m_localTime.localtime(&now);

    if (localTime != nullptr)
    {
        hour = localTime->tm_hour;
    }

    return hour;
}

/******************************************************************************
 * External Functions
 *****************************************************************************/

/******************************************************************************
 * Local Functions
 *****************************************************************************/
