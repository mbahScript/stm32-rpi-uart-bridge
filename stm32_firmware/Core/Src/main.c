/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : STM32F767 ↔ RPi5 UART Transport Protocol (USART3)
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "string.h"
#include "stdio.h"
#include <stdlib.h>   // strtoul(), atoi()
/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

UART_HandleTypeDef huart3;

/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART3_UART_Init(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* ========= Protocol Settings ========= */
#define STX 0x02
#define ETX 0x03

#define RX_BUFFER_SIZE 192
#define TX_BUFFER_SIZE 256

/* ========= Node Identity ========= */
static char NODE_ID[16] = "BUS01";
static char ROUTE_ID[16] = "25B";
static int  CURRENT_ETA = 3;

/* ========= UART RX State ========= */
static uint8_t rx_byte;
static char rx_buffer[RX_BUFFER_SIZE];
static uint16_t rx_index = 0;
static uint8_t receiving = 0;

/* ========= Timing ========= */
static uint32_t last_hb_ms = 0;
static uint32_t last_arr_ms = 0;
static uint32_t last_dl_ms = 0;

/**
 * @brief XOR checksum of ASCII payload (bytes between STX and before checksum field)
 */
static uint8_t checksum_xor(const char *data)
{
    uint8_t chk = 0;
    while (*data)
    {
        chk ^= (uint8_t)(*data);
        data++;
    }
    return chk;
}

/**
 * @brief Build and send framed packet: <STX>TYPE|NODE|DATA|CHK<ETX>
 * @param type 3-6 chars suggested (e.g., "HB", "ARR", "DL", "ACK", "STATUS", "ERR", "CMD")
 * @param node node identifier (e.g., "BUS01")
 * @param data payload text (no ETX/STX), can be empty string ""
 */

// NOTE: TX_BUFFER_SIZE should comfortably fit: STX + TYPE|NODE|DATA|CHK + ETX
// Increase if you add longer DATA payloads later (e.g., multi-stop updates).

static void send_packet(const char *type, const char *node, const char *data)
{
    char payload[TX_BUFFER_SIZE];
    char frame[TX_BUFFER_SIZE];

    int n = snprintf(payload, sizeof(payload), "%s|%s|%s", type, node, data);
    if (n < 0 || n >= (int)sizeof(payload)) {
        // Payload too long
        const char err[] = {STX,'E','R','R','|','B','U','S','0','1','|','T','X','_','T','O','O','_','L','O','N','G','|','0','0',ETX};
        HAL_UART_Transmit(&huart3, (uint8_t*)err, sizeof(err), HAL_MAX_DELAY);
        return;
    }

    uint8_t chk = checksum_xor(payload);

    n = snprintf(frame, sizeof(frame), "%c%s|%02X%c", STX, payload, chk, ETX);
    if (n < 0 || n >= (int)sizeof(frame)) {
        // Frame too long
        const char err[] = {STX,'E','R','R','|','B','U','S','0','1','|','F','R','M','_','T','O','O','_','L','O','N','G','|','0','0',ETX};
        HAL_UART_Transmit(&huart3, (uint8_t*)err, sizeof(err), HAL_MAX_DELAY);
        return;
    }

    HAL_UART_Transmit(&huart3, (uint8_t*)frame, (uint16_t)strlen(frame), HAL_MAX_DELAY);
}

/**
 * @brief Parse command payload and respond
 * Expected CMD packet payload format: CMD|HOST|<command>
 * Here we treat incoming rx_buffer content as: TYPE|NODE|DATA|CHK  (without STX/ETX)
 */
static void handle_complete_message(const char *msg)
{
    char copy[RX_BUFFER_SIZE];
    strncpy(copy, msg, sizeof(copy)-1);
    copy[sizeof(copy)-1] = '\0';

    // 1) Find LAST '|' which separates checksum from the rest
    char *last_bar = strrchr(copy, '|');
    if (!last_bar) {
        send_packet("ERR", NODE_ID, "FORMAT");
        return;
    }

    // last_bar points to '|' before checksum
    char *chk_str = last_bar + 1;
    *last_bar = '\0';  // Now copy becomes: "TYPE|NODE|DATA"

    // 2) Validate checksum using the remaining string (TYPE|NODE|DATA)
    uint8_t calc_chk = checksum_xor(copy);
    uint8_t recv_chk = (uint8_t)strtoul(chk_str, NULL, 16);

    if (calc_chk != recv_chk) {
        send_packet("ERR", NODE_ID, "CHK");
        return;
    }

    // 3) Extract TYPE
    char *type = strtok(copy, "|");
    char *node = strtok(NULL, "|");

    // 4) DATA is whatever remains after TYPE and NODE
    char *data = strtok(NULL, "");  // rest of string
    if (!type || !node || !data) {
        send_packet("ERR", NODE_ID, "FORMAT");
        return;
    }

    // Handle CMD
    if (strcmp(type, "CMD") == 0)
    {
        if (strcmp(data, "PING") == 0) {
            send_packet("ACK", NODE_ID, "PONG");
        }
        else if (strcmp(data, "STATUS") == 0) {
            char info[80];
            snprintf(info, sizeof(info), "NODE=%s,ROUTE=%s,ETA=%d", NODE_ID, ROUTE_ID, CURRENT_ETA);
            send_packet("STATUS", NODE_ID, info);
        }
        else if (strncmp(data, "SETROUTE=", 9) == 0) {
            strncpy(ROUTE_ID, data + 9, sizeof(ROUTE_ID)-1);
            ROUTE_ID[sizeof(ROUTE_ID)-1] = '\0';
            send_packet("ACK", NODE_ID, "ROUTE_SET");
        }
        else if (strncmp(data, "SETETA=", 7) == 0) {
            CURRENT_ETA = atoi(data + 7);
            send_packet("ACK", NODE_ID, "ETA_SET");
        }
        else {
            send_packet("ERR", NODE_ID, "UNKNOWN_CMD");
        }
    }
    else {
        send_packet("ERR", NODE_ID, "UNKNOWN_TYPE");
    }
}


/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_USART3_UART_Init();
  /* USER CODE BEGIN 2 */

  /* Start interrupt-driven RX (1 byte at a time) */
  HAL_UART_Receive_IT(&huart3, &rx_byte, 1);

  /* Initialize timers */
  uint32_t now = HAL_GetTick();
  last_hb_ms  = now;
  last_arr_ms = now;
  last_dl_ms  = now;
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */
	    /* USER CODE BEGIN 3 */
	    uint32_t t = HAL_GetTick();

	    /* Heartbeat every 5 seconds */
	    if ((t - last_hb_ms) >= 5000)
	    {
	        last_hb_ms = t;
	        send_packet("HB", NODE_ID, "OK");
	    }

	    /* Arrival update every 10 seconds */
	    if ((t - last_arr_ms) >= 10000)
	    {
	        last_arr_ms = t;

	        char data[80];
	        snprintf(data, sizeof(data), "ROUTE=%s,STOP=STOP12,ETA=%d", ROUTE_ID, CURRENT_ETA);
	        send_packet("ARR", NODE_ID, data);
	    }

	    /* Delay event (demo) every 30 seconds */
	    if ((t - last_dl_ms) >= 30000)
	    {
	        last_dl_ms = t;
	        send_packet("DL", NODE_ID, "+5MIN");
	    }

	    /* Main loop stays free; RX handled in interrupt callback */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE3);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLM = 4;
  RCC_OscInitStruct.PLL.PLLN = 96;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = 4;
  RCC_OscInitStruct.PLL.PLLR = 2;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Activate the Over-Drive mode
  */
  if (HAL_PWREx_EnableOverDrive() != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_3) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief USART3 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART3_UART_Init(void)
{

  /* USER CODE BEGIN USART3_Init 0 */

  /* USER CODE END USART3_Init 0 */

  /* USER CODE BEGIN USART3_Init 1 */

  /* USER CODE END USART3_Init 1 */
  huart3.Instance = USART3;
  huart3.Init.BaudRate = 115200;
  huart3.Init.WordLength = UART_WORDLENGTH_8B;
  huart3.Init.StopBits = UART_STOPBITS_1;
  huart3.Init.Parity = UART_PARITY_NONE;
  huart3.Init.Mode = UART_MODE_TX_RX;
  huart3.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart3.Init.OverSampling = UART_OVERSAMPLING_16;
  huart3.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
  huart3.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
  if (HAL_UART_Init(&huart3) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART3_Init 2 */

  /* USER CODE END USART3_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
/* USER CODE BEGIN MX_GPIO_Init_1 */
   GPIO_InitTypeDef GPIO_InitStruct = {0};
/* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOH_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_USART3_CLK_ENABLE();

/* USER CODE BEGIN MX_GPIO_Init_2 */
  /* USART3 TX PB10 */
  GPIO_InitStruct.Pin = GPIO_PIN_10;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
  GPIO_InitStruct.Alternate = GPIO_AF7_USART3;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /* USART3 RX PB11 */
  GPIO_InitStruct.Pin = GPIO_PIN_11;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  GPIO_InitStruct.Alternate = GPIO_AF7_USART3;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);
/* USER CODE BEGIN MX_GPIO_Init_2 */
/* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */
/**
 * @brief UART RX complete callback (interrupt-driven)
 * This assembles framed messages between STX and ETX into rx_buffer.
 * On ETX, it calls handle_complete_message(rx_buffer)
 */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART3)
    {
        if (rx_byte == STX)
        {
            receiving = 1;
            rx_index = 0;
        }
        else if ((rx_byte == ETX) && receiving)
        {
            rx_buffer[rx_index] = '\0';
            receiving = 0;

            /* rx_buffer contains: TYPE|NODE|DATA|CHK */
            handle_complete_message(rx_buffer);

            rx_index = 0;
        }
        else if (receiving)
        {
            if (rx_index < (RX_BUFFER_SIZE - 1))
            {
                rx_buffer[rx_index++] = (char)rx_byte;
            }
            else
            {
                /* Overflow: reset state safely */
                receiving = 0;
                rx_index = 0;
                send_packet("ERR", NODE_ID, "RX_OVERFLOW");
            }
        }

        /* Re-arm RX interrupt for next byte */
        HAL_UART_Receive_IT(&huart3, &rx_byte, 1);
    }
}

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
