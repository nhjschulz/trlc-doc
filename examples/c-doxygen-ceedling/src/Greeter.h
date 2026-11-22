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
 * @brief  Greeter
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
#include <stdint.h>

/******************************************************************************
 * Macros
 *****************************************************************************/

/******************************************************************************
 * Types and Classes
 *****************************************************************************/

/******************************************************************************
 * Functions
 *****************************************************************************/

/**
 * @brief Initialize the greeter and configure the different time thresholds.
 *
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
extern void Greeter_init(int hourThresholdMorning, int hourThresholdMidday, int hourThresholdAfternoon, int hourThresholdNight);

/**
 * @brief Greet the given user dependent on the current time.
 *
 * @param[in] userName  A name to greet or None to use the login name.
 *
 * @implements{SwRequirements.sw_req_cli_default_name}
 * @implements{SwRequirements.sw_func_morning_time_greeting}
 * @implements{SwRequirements.sw_func_midday_time_greeting}
 * @implements{SwRequirements.sw_func_afternoon_time_greeting}
 * @implements{SwRequirements.sw_func_night_time_greeting}
 */
extern void Greeter_greet(const char* userName);

#endif /* GREETER_H */

/** @} */
