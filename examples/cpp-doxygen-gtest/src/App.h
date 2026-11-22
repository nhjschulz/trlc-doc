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
 * @file   App.h
 * @brief  Application
 * @author Andreas Merkle <web@blue-andi.de>
 *
 * @addtogroup APP
 *
 * @{
 */

#ifndef APP_H
#define APP_H

/******************************************************************************
 * Compile Switches
 *****************************************************************************/

/******************************************************************************
 * Includes
 *****************************************************************************/
#include <string>

/******************************************************************************
 * Macros
 *****************************************************************************/

/******************************************************************************
 * Types and Classes
 *****************************************************************************/

/**
 * @brief The application class handles the whole application.
 * It encapsulates the main functionality of the application to support the
 * testing.
 */
class App
{
public:

    /**
     * @brief Construct a new App object.
     *
     * @implements{SwRequirements.sw_req_cli}
     */
    App()
    {
        /* Nothing to do. */
    }

    /**
     * @brief Destroy the App object.
     *
     * @justification{Destructors don't get requirements assigned.}
     */
    ~App()
    {
        /* Nothing to do. */
    }

    /**
     * @brief Run the application.
     *
     * @param[in] argc  Number of command line arguments.
     * @param[in] argv  Command line arguments.
     *
     * @return 0 if handling was successful. Otherwise, 1.
     *
     * @implements{SwRequirements.sw_req_cli}
     * @implements{SwRequirements.sw_func_msg_output}
     */
    int run(int argc, char** argv);

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

private:

    /**
     * @brief Program description
     */
    static const char* PROG_DESC;

    /**
     * @brief Program copyright
     */
    static const char* PROG_COPYRIGHT;

    /**
     * @brief This type defines the possible program arguments.
     *
     * @implements{SwRequirements.sw_req_cli_user_name}
     */
    struct PrgArguments
    {
        const char* progName; /**< Program name. */
        const char* userName; /**< User name to use for greeting. */
    };

    /**
     * @brief Not allowed.
     *
     * @justification{The copy constructor is not allowed, because the class is not intended to be copied.}
     */
    App(const App&)            = delete;

    /**
     * @brief Not allowed.
     *
     * @justification{The assignment operator is not allowed, because the class is not intended to be copied.}
     */
    App& operator=(const App&) = delete;

    /**
     * @brief Print an info message to stdout.
     *
     * @param[in] format    Format string for the info message.
     * @param[in] ...       Arguments for the format string
     *
     * @implements{SwRequirements.sw_func_msg_output}
     */
    void printInfo(const char* format, ...);

    /**
     * @brief Print an error message to stderr.
     *
     * @param[in] format    Format string for the error message.
     * @param[in] ...       Arguments for the format string
     *
     * @implements{SwRequirements.sw_req_cli_usage_error}
     */
    void printError(const char* format, ...);

    /**
     * @brief Handle the arguments passed to the programm.
     * If a argument is not given via command line interface, its default value will be used.
     *
     * @param[out]  prgArguments    Parsed program arguments
     * @param[in]   argc            Program argument count
     * @param[in]   argv            Program argument vector
     *
     * @returns 0 if handling was succesful. Otherwise, -1
     *
     * @implements{SwRequirements.sw_req_cli_help}
     * @implements{SwRequirements.sw_req_cli_user_name}
     * @implements{SwRequirements.sw_req_cli_usage_error}
     */
    int handleCommandLineArguments(PrgArguments& prgArguments, int argc, char** argv);
};

/******************************************************************************
 * Functions
 *****************************************************************************/

#endif /* APP_H */

/** @} */
