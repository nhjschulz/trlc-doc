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
 * @file   App.c
 * @brief  The main application.
 * @author Andreas Merkle <web@blue-andi.de>
 */

/******************************************************************************
 * Includes
 *****************************************************************************/
#include <stdio.h>
#include <stdarg.h>
#include <getopt.h>
#include "Greeter.h"
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

/**
 * @brief This type defines the possible program arguments.
 *
 * @implements{SwRequirements.sw_req_cli_user_name}
 */
typedef struct
{
    const char* progName; /**< Program name. */
    const char* userName; /**< User name to use for greeting. */

} PrgArguments;

/******************************************************************************
 * Prototypes
 *****************************************************************************/

static int  handleCommandLineArguments(PrgArguments* prgArguments, int argc, char** argv);

/******************************************************************************
 * Local Variables
 *****************************************************************************/

/**
 * @brief Program description used for CLI help command.
 */
static const char* PROG_DESC              = "A C CLI tool to greet a user considering the time.";

/**
 * @brief Program copyright used for CLI helpt and version command.
 */
static const char* PROG_COPYRIGHT         = "Copyright (c) 2025 NewTec GmbH";

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

int App_run(int argc, char** argv)
{
    int          status = 0; /* Status */
    PrgArguments prgArguments;

    /* Remove any buffering from stout and stderr to get the printed information immediately. */
    (void)setvbuf(stdout, NULL, _IONBF, 0);
    (void)setvbuf(stderr, NULL, _IONBF, 0);

    status = handleCommandLineArguments(&prgArguments, argc, argv);

    if (0 == status)
    {
        Greeter_init(HOUR_THRESHOLD_MORNING,
            HOUR_THRESHOLD_MIDDAY,
            HOUR_THRESHOLD_AFTERNOON,
            HOUR_THRESHOLD_NIGHT);

        Greeter_greet(prgArguments.userName);
    }

    return status;
}

/******************************************************************************
 * Local Functions
 *****************************************************************************/

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
static int handleCommandLineArguments(PrgArguments* prgArguments, int argc, char** argv)
{
    const struct option LONG_OPTIONS[] = {
        { "help", no_argument, NULL, 'h' },
        { NULL, no_argument, NULL, 0 } /* Marks the end. */
    };
    int         status       = 0;
    const char* shortOptions = ":h";
    int         optionIndex  = 0;
    int         option       = getopt_long(argc, argv, shortOptions, LONG_OPTIONS, &optionIndex);

    if (NULL == prgArguments)
    {
        status = -1;
    }
    else
    {
        /* Set default values */
        prgArguments->progName = argv[0];
        prgArguments->userName = NULL;

        while ((-1 != option) && (0 == status))
        {
            switch (option)
            {
            case '?': /* Unknown */
                Printer_printError("Error: Unknown option: %s\n\n", argv[optind - 1]);
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
            prgArguments->userName = argv[optind];
        }

        /* Does the user need help? */
        if (0 > status)
        {
            Printer_printInfo("%s\n", PROG_DESC);
            Printer_printInfo("Usage: %s <option(s)> [NAME]\n", prgArguments->progName);
            Printer_printInfo("\tArguments:\n");
            Printer_printInfo("\t\tNAME\t\tSpecify a user name to greet, defaults to login name if unset.\n"); /* Name */
            Printer_printInfo("\tOptions:\n");
            Printer_printInfo("\t\t--help, -h\tShow this help message.\n"); /* Help */
            Printer_printInfo("\n");
            Printer_printInfo("%s\n", PROG_COPYRIGHT);
        }
    }

    return status;
}
