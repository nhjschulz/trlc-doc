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
 * @file   ILocalTime.h
 * @brief  LocalTime interface
 * @author Luca Dubies <luca.dubies@newtec.de>
 *
 * @addtogroup APP
 *
 * @{
 */

#ifndef I_LOCAL_TIME_H
#define I_LOCAL_TIME_H

/******************************************************************************
 * Compile Switches
 *****************************************************************************/

/******************************************************************************
 * Includes
 *****************************************************************************/
#include <time.h>

/******************************************************************************
 * Macros
 *****************************************************************************/

/******************************************************************************
 * Types and Classes
 *****************************************************************************/

/**
 * @brief The local time interface describes an interface to time related system calls.
 */
class ILocalTime
{
public:
    /**
     * @brief Destroys the local time interface.
     * 
     * @implements{SwRequirements.sw_func_daytime_greeting_selection}
     */
    virtual ~ILocalTime()
    {
    }

    /**
     * @brief Provide the current time in Unix epoch.
     * 
     * @param[in] timeVar   Pointer to a time_t variable to store the current time.
     * 
     * @return Unix epoch (seconds elapsed since 1970.01.01)
     * 
     * @justification{System call.}
     */
    virtual time_t time(time_t* timeVar) const = 0;
    
    /**
     * @brief Converts a unix timestamp to a time struct containing local time information.
     * 
     * @param[in] timeVar   Pointer to a time_t variable to convert to local time.
     * 
     * @return Pointer to local time data.
     * 
     * @justification{System call.}
     */
    virtual tm* localtime(const time_t* timeVar) const = 0;

protected:

    /**
     * @brief Constructs the local time interface.
     * 
     * @justification{Constructors don't get requirements assigned.}
     */
    ILocalTime()
    {
    }
};

/******************************************************************************
 * Functions
 *****************************************************************************/

#endif /* I_LOCAL_TIME_H */

/** @} */
