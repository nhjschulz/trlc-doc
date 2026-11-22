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
 *
 * @addtogroup TEST
 *
 * @{
 */

#ifndef STUB_PRINTER_H
#define STUB_PRINTER_H

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
 * @brief Print message to stdout.
 *
 * @param[in] format    Format string for the message.
 * @param[in] ...       Arguments for the format string
 */
extern void Printer_printf(const char* format, ...);

/**
 * @brief Print an info message to stdout.
 *
 * @param[in] format    Format string for the info message.
 * @param[in] ...       Arguments for the format string
 */
extern void Printer_printInfo(const char* format, ...);

/**
 * @brief Print an error message to stderr.
 *
 * @param[in] format    Format string for the error message.
 * @param[in] ...       Arguments for the format string
 */
extern void Printer_printError(const char* format, ...);

/**
 * @brief Initialize test with capture buffer.
 * 
 * @param[in] bufferStdout      The capture buffer for stdout.
 * @param[in] bufferStdoutSize  The size of the stdout capture buffer in byte.
 * @param[in] bufferStderr      The capture buffer for stderr.
 * @param[in] bufferStderrSize  The size of the stderr capture buffer in byte.
 */
extern void Printer_testInit(char* bufferStdout, size_t bufferStdoutSize, char* bufferStderr, size_t bufferStderrSize);

/**
 * @brief Clear the stdout capture buffer.
 */
extern void Printer_testClearBufferStdout(void);

/**
 * @brief Clear the stderr capture buffer.
 */
extern void Printer_testClearBufferStderr(void);

/**
 * @brief Get the stdout capture buffer.
 * 
 * @param[out] written  Number of written characters to the capture buffer (optional).
 * @param[out] size     Size of the capture buffer in byte (optional).
 * 
 * @return Pointer to capture buffer
 */
extern const char* Printer_testGetBufferStdout(size_t* written, size_t* size);

/**
 * @brief Get the stderr capture buffer.
 * 
 * @param[out] written  Number of written characters to the capture buffer (optional).
 * @param[out] size     Size of the capture buffer in byte (optional).
 * 
 * @return Pointer to capture buffer
 */
extern const char* Printer_testGetBufferStderr(size_t* written, size_t* size);

#endif /* STUB_PRINTER_H */

/** @} */
