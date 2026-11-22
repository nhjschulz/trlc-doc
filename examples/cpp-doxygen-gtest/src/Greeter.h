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
 * @file   Greeter.h
 * @brief  Greeter class
 * @author Andreas Merkle <web@blue-andi.de>
 *
 * @addtogroup APP
 *
 * @{
 */

#ifndef GREETER_H
#define GREETER_H

/******************************************************************************
 * Compile Switches
 *****************************************************************************/

/******************************************************************************
 * Includes
 *****************************************************************************/
#include <string>
#include "ILocalTime.h"

/******************************************************************************
 * Macros
 *****************************************************************************/

/******************************************************************************
 * Types and Classes
 *****************************************************************************/

/**
 * @brief The greeter class greets a user depending on the time of day.
 */
class Greeter
{
public:

    /**
     * @brief Construct a new Greeter object.
     *
     * @param[in] localTime               An interface to access time system calls.
     * @param[in] hourThresholdMorning    Hour threshold for morning.
     * @param[in] hourThresholdMidday     Hour threshold for midday.
     * @param[in] hourThresholdAfternoon  Hour threshold for afternoon.
     * @param[in] hourThresholdNight      Hour threshold for night.
     *
     * @implements{SwRequirements.sw_req_cli_default_name}
     * @implements{SwRequirements.sw_func_morning_time_greeting}
     * @implements{SwRequirements.sw_func_midday_time_greeting}
     * @implements{SwRequirements.sw_func_afternoon_time_greeting}
     * @implements{SwRequirements.sw_func_night_time_greeting}
     */
    Greeter(const ILocalTime& localTime, int hourThresholdMorning, int hourThresholdMidday, int hourThresholdAfternoon, int hourThresholdNight) :
        m_localTime(localTime),
        m_hourThresholdMorning(hourThresholdMorning),
        m_hourThresholdMidday(hourThresholdMidday),
        m_hourThresholdAfternoon(hourThresholdAfternoon),
        m_hourThresholdNight(hourThresholdNight)
    {
        /* Nothing to do. */
    }

    /**
     * @brief Destroy the Greeter object.
     *
     * @justification{Destructors don't get requirements assigned.}
     */
    ~Greeter()
    {
        /* Nothing to do. */
    }

    /**
     * @brief Greet the given user dependent on the current time.
     *
     * @param[in] userName  A name to greet or None to use the login name.
     *
     * @return A greeting message for the user.
     *
     * @implements{SwRequirements.sw_req_cli_default_name}
     * @implements{SwRequirements.sw_func_morning_time_greeting}
     * @implements{SwRequirements.sw_func_midday_time_greeting}
     * @implements{SwRequirements.sw_func_afternoon_time_greeting}
     * @implements{SwRequirements.sw_func_night_time_greeting}
     */
    std::string greet(const char* userName);

private:

    const ILocalTime& m_localTime;              /**< An interface to access time system calls. */
    int               m_hourThresholdMorning;   /**< Hour threshold for morning. */
    int               m_hourThresholdMidday;    /**< Hour threshold for midday. */
    int               m_hourThresholdAfternoon; /**< Hour threshold for afternoon. */
    int               m_hourThresholdNight;     /**< Hour threshold for night. */

    /**
     * @brief Get the current hour of the day.
     *
     * @returns Current hour of the day.
     *
     * @implements{SwRequirements.sw_func_daytime_greeting_selection}
     */
    int getHourOfDay() const;

    /**
     * @brief Not allowwed.
     *
     * @justification{The copy constructor is not allowed, because the class is not intended to be copied.}
     */
    Greeter(const Greeter&)            = delete;

    /**
     * @brief Not allowed.
     *
     * @justification{The assignment operator is not allowed, because the class is not intended to be copied.}
     */
    Greeter& operator=(const Greeter&) = delete;

    /**
     * @brief Get the user login name.
     *
     * @return User login name or nullptr if not available.
     *
     * @implements{SwRequirements.sw_req_cli_default_name}
     */
    const char* getUserName() const;
};

/******************************************************************************
 * Functions
 *****************************************************************************/

#endif /* GREETER_H */

/** @} */
