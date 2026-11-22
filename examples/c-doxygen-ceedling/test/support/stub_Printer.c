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
 * @file   Printer.h
 * @brief  Abstracts the system stdio calls.
 * @author Andreas Merkle <web@blue-andi.de>
 */

/******************************************************************************
 * Includes
 *****************************************************************************/
#include "Printer.h"
#include "unity.h"
#include <stdarg.h>
#include <memory.h>

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

/**
 * @brief Buffer used to capture the stdout printed characters.
 */
static char* gCaptureBufferStdout            = NULL;

/**
 * @brief Size of the stdout capture buffer in byte.
 */
static size_t gCaptureBufferStdoutSize       = 0U;

/**
 * @brief The write index to the stdout capture buffer, used to continously write to it.
 */
static size_t gCaptureBufferStdoutWriteIndex = 0U;

/**
 * @brief Buffer used to capture the stderr printed characters.
 */
static char* gCaptureBufferStderr            = NULL;

/**
 * @brief Size of the stderr capture buffer in byte.
 */
static size_t gCaptureBufferStderrSize       = 0U;

/**
 * @brief The write index to the stderr capture buffer, used to continously write to it.
 */
static size_t gCaptureBufferStderrWriteIndex = 0U;

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

void Printer_printf(const char* format, ...)
{
    va_list args;

    (void)va_start(args, format);

    if ((NULL != gCaptureBufferStdout) && (0U < gCaptureBufferStdoutSize))
    {
        gCaptureBufferStdoutWriteIndex += vsnprintf(
            &gCaptureBufferStdout[gCaptureBufferStdoutWriteIndex],
            gCaptureBufferStdoutSize - gCaptureBufferStdoutWriteIndex,
            format,
            args);
    }

    (void)va_end(args);
}

extern void Printer_printInfo(const char* format, ...)
{
    va_list args;

    (void)va_start(args, format);

    if ((NULL != gCaptureBufferStdout) && (0U < gCaptureBufferStdoutSize))
    {
        gCaptureBufferStdoutWriteIndex += vsnprintf(
            &gCaptureBufferStdout[gCaptureBufferStdoutWriteIndex],
            gCaptureBufferStdoutSize - gCaptureBufferStdoutWriteIndex,
            format,
            args);
    }

    (void)va_end(args);
}

extern void Printer_printError(const char* format, ...)
{
    va_list args;

    (void)va_start(args, format);

    if ((NULL != gCaptureBufferStderr) && (0U < gCaptureBufferStderrSize))
    {
        gCaptureBufferStderrWriteIndex += vsnprintf(
            &gCaptureBufferStderr[gCaptureBufferStderrWriteIndex],
            gCaptureBufferStderrSize - gCaptureBufferStderrWriteIndex,
            format,
            args);
    }

    (void)va_end(args);
}

void Printer_testInit(char* bufferStdout, size_t bufferStdoutSize, char* bufferStderr, size_t bufferStderrSize)
{
    gCaptureBufferStdout           = bufferStdout;
    gCaptureBufferStdoutSize       = bufferStdoutSize;
    gCaptureBufferStdoutWriteIndex = 0U;

    gCaptureBufferStderr           = bufferStderr;
    gCaptureBufferStderrSize       = bufferStderrSize;
    gCaptureBufferStderrWriteIndex = 0U;
}

void Printer_testClearBufferStdout(void)
{
    gCaptureBufferStdoutWriteIndex = 0U;

    if (NULL != gCaptureBufferStdout)
    {
        memset(gCaptureBufferStdout, 0xCC, gCaptureBufferStdoutSize);
    }
}

void Printer_testClearBufferStderr(void)
{
    gCaptureBufferStderrWriteIndex = 0U;

    if (NULL != gCaptureBufferStderr)
    {
        memset(gCaptureBufferStderr, 0xCC, gCaptureBufferStderrSize);
    }
}

const char* Printer_testGetBufferStdout(size_t* written, size_t* size)
{
    if (NULL != written)
    {
        *written = gCaptureBufferStdoutWriteIndex;
    }

    if (NULL != size)
    {
        *size = gCaptureBufferStdoutSize;
    }

    return gCaptureBufferStdout;
}

const char* Printer_testGetBufferStderr(size_t* written, size_t* size)
{
    if (NULL != written)
    {
        *written = gCaptureBufferStderrWriteIndex;
    }

    if (NULL != size)
    {
        *size = gCaptureBufferStderrSize;
    }

    return gCaptureBufferStderr;
}

/******************************************************************************
 * Local Functions
 *****************************************************************************/
