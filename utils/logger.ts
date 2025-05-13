/**
 * Logging utility for the Medical Terminology Mapper.
 * Provides centralized logging functionality with different levels and formats.
 * Adapted from the Clinical Protocol Extractor project.
 */

import * as fs from 'fs';
import * as path from 'path';
import * as winston from 'winston';

/**
 * Setup logger with console and file handlers
 * 
 * @param name - Logger name
 * @param logFile - Path to log file (optional)
 * @param level - Logging level
 * @returns Configured logger instance
 */
export function setupLogger(name: string, logFile?: string, level: string = 'info'): winston.Logger {
  // Create logger
  const logger = winston.createLogger({
    level: level,
    format: winston.format.combine(
      winston.format.timestamp({
        format: 'YYYY-MM-DD HH:mm:ss'
      }),
      winston.format.printf(info => `${info.timestamp} - ${name} - ${info.level}: ${info.message}`)
    ),
    transports: [
      new winston.transports.Console()
    ]
  });

  // Create file handler if log file is specified
  if (logFile) {
    // Ensure log directory exists
    const logDir = path.dirname(logFile);
    if (logDir && !fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }

    // Add file transport
    logger.add(new winston.transports.File({ 
      filename: logFile,
      maxsize: 10 * 1024 * 1024, // 10MB
      maxFiles: 5
    }));
  }

  return logger;
}

/**
 * Setup specialized logger for performance metrics
 * 
 * @param name - Logger name
 * @param logDir - Directory for log files
 * @returns Configured performance logger
 */
export function getPerformanceLogger(name: string = 'performance', logDir?: string): winston.Logger {
  // Default log directory if not specified
  if (!logDir) {
    logDir = path.join(path.dirname(path.dirname(__dirname)), 'logs');
  }

  // Ensure log directory exists
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }

  // Create logger with simplified format for metrics
  const perfLogger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
      winston.format.timestamp({
        format: 'YYYY-MM-DD HH:mm:ss'
      }),
      winston.format.printf(info => `${info.timestamp} - ${info.message}`)
    ),
    transports: [
      new winston.transports.File({
        filename: path.join(logDir, `${name}.log`),
        maxsize: 5 * 1024 * 1024, // 5MB
        maxFiles: 3
      })
    ]
  });

  return perfLogger;
}

/**
 * Setup specialized logger for error tracking
 * 
 * @param name - Logger name
 * @param logDir - Directory for log files
 * @returns Configured error logger
 */
export function getErrorLogger(name: string = 'error', logDir?: string): winston.Logger {
  // Default log directory if not specified
  if (!logDir) {
    logDir = path.join(path.dirname(path.dirname(__dirname)), 'logs');
  }

  // Ensure log directory exists
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }

  // Create detailed format for errors
  const errorFormat = winston.format.combine(
    winston.format.timestamp({
      format: 'YYYY-MM-DD HH:mm:ss'
    }),
    winston.format.errors({ stack: true }),
    winston.format.printf(info => 
      `${info.timestamp} - ${name} - ${info.level}: ${info.message}${info.stack ? '\n' + info.stack : ''}`)
  );

  // Create logger
  const errorLogger = winston.createLogger({
    level: 'error',
    format: errorFormat,
    transports: [
      new winston.transports.Console(),
      new winston.transports.File({
        filename: path.join(logDir, `${name}.log`),
        maxsize: 5 * 1024 * 1024, // 5MB
        maxFiles: 10
      })
    ]
  });

  return errorLogger;
}

/**
 * Configure the root logger for application-wide logging
 * 
 * @param logDir - Directory for log files
 * @param level - Logging level
 */
export function configureRootLogger(logDir?: string, level: string = 'info'): winston.Logger {
  // Default log directory if not specified
  if (!logDir) {
    logDir = path.join(path.dirname(path.dirname(__dirname)), 'logs');
  }

  // Ensure log directory exists
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }

  // Get current date for log filename
  const today = new Date().toISOString().split('T')[0];
  
  // Create root logger
  const rootLogger = winston.createLogger({
    level: level,
    format: winston.format.combine(
      winston.format.timestamp({
        format: 'YYYY-MM-DD HH:mm:ss'
      }),
      winston.format.printf(info => 
        `${info.timestamp} - ${info.level}: ${info.message}`)
    ),
    transports: [
      new winston.transports.Console(),
      new winston.transports.File({
        filename: path.join(logDir, `app_${today}.log`),
        maxsize: 10 * 1024 * 1024, // 10MB
        maxFiles: 10
      })
    ]
  });

  // Log startup message
  rootLogger.info('Logger initialized');

  return rootLogger;
}

export default {
  setupLogger,
  getPerformanceLogger,
  getErrorLogger,
  configureRootLogger
};