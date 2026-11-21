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
 * @file   App.cpp
 * @brief  App class
 * @author Andreas Merkle <web@blue-andi.de>
 */

/******************************************************************************
 * Includes
 *****************************************************************************/
#include "App.h"
#include <stdio.h>
#include <getopt.h>
#include <string.h>
#include <stdarg.h>
#include "Greeter.h"
#include "LocalTime.h"

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

const char* App::PROG_DESC      = "A C++ CLI tool to greet a user considering the time.";
const char* App::PROG_COPYRIGHT = "Copyright (c) 2025 NewTec GmbH";

/******************************************************************************
 * Public Methods
 *****************************************************************************/

int App::run(int argc, char** argv)
{
    int          status = 0; /* Status */
    PrgArguments prgArguments;

    /* Remove any buffering from stout and stderr to get the printed information immediately. */
    (void)setvbuf(stdout, NULL, _IONBF, 0);
    (void)setvbuf(stderr, NULL, _IONBF, 0);

    status = handleCommandLineArguments(prgArguments, argc, argv);

    if (0 == status)
    {
        LocalTime localTime;
        Greeter   greeter(
            localTime,
            HOUR_THRESHOLD_MORNING,
            HOUR_THRESHOLD_MIDDAY,
            HOUR_THRESHOLD_AFTERNOON,
            HOUR_THRESHOLD_NIGHT);

        std::string greeting = greeter.greet(prgArguments.userName);

        printInfo("%s\n", greeting.c_str());
    }

    return status;
}

/******************************************************************************
 * Protected Methods
 *****************************************************************************/

/******************************************************************************
 * Private Methods
 *****************************************************************************/

void App::printInfo(const char* format, ...)
{
    va_list args;

    va_start(args, format);
    vfprintf(stdout, format, args);
    va_end(args);
}

void App::printError(const char* format, ...)
{
    va_list args;

    va_start(args, format);
    vfprintf(stderr, format, args);
    va_end(args);
}

int App::handleCommandLineArguments(PrgArguments& prgArguments, int argc, char** argv)
{
    const struct option LONG_OPTIONS[] = {
        { "help", no_argument, nullptr, 'h' },
        { nullptr, no_argument, nullptr, 0 } /* Marks the end. */
    };
    int         status       = 0;
    const char* shortOptions = ":h";
    int         optionIndex  = 0;
    int         option       = getopt_long(argc, argv, shortOptions, LONG_OPTIONS, &optionIndex);

    /* Set default values */
    prgArguments.progName    = argv[0];
    prgArguments.userName    = nullptr;

    while ((-1 != option) && (0 == status))
    {
        switch (option)
        {
        case '?': /* Unknown */
            printError("Error: Unknown option: %s\n\n", argv[optind - 1]);
            /* fallthrough */

        case 'h': /* Help */
            /* fallthrough */

        default: /* Default */
            status = -1;
            break;
        }

        option = getopt_long(argc, argv, shortOptions, LONG_OPTIONS, &optionIndex);
    }

    /* Get the user name argument. */
    if ((0 == status) && (optind < argc))
    {
        prgArguments.userName = argv[optind];
    }

    /* Does the user need help? */
    if (0 > status)
    {
        printInfo("%s\n", PROG_DESC);
        printInfo("Usage: %s <option(s)> [NAME]\n", prgArguments.progName);
        printInfo("\tArguments:\n");
        printInfo("\t\tNAME\t\tSpecify a user name to greet, defaults to login name if unset.\n"); /* Name */
        printInfo("\tOptions:\n");
        printInfo("\t\t--help, -h\tShow this help message.\n"); /* Help */
        printInfo("\n");
        printInfo("%s\n", PROG_COPYRIGHT);
    }

    return status;
}

/******************************************************************************
 * External Functions
 *****************************************************************************/

/******************************************************************************
 * Local Functions
 *****************************************************************************/
