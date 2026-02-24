/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : STM32F767 ↔ RPi5 UART Transport Protocol v0.3.0 (USART3)
  ******************************************************************************
  * Protocol v2: <STX>TYPE|NODE|SEQ|DATA|CHK<ETX>
  * - STX = 0x02, ETX = 0x03
  * - CHK = XOR over ASCII bytes of "TYPE|NODE|SEQ|DATA"
  *
  * Telemetry frames use auto-incrementing SEQ.
  * Replies to HOST commands echo the HOST SEQ so the Pi can match responses.
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
//#define TX_BUFFER_SIZE 256

/* ========= Node Identity ========= */
static char NODE_ID[16] = "BUS01";
static char ROUTE_ID[16] = "25B";
static int  CURRENT_ETA = 3;

/* ========= UART RX State ========= */
static uint8_t rx_byte;
static char rx_buffer[RX_BUFFER_SIZE];
static uint16_t rx_index = 0;
static uint8_t receiving = 0;

/* ========= UART TX Sequence ========= */
static uint8_t tx_seq = 0;

/* ========= Duplicate Detection (HOST CMDs) ========= */
static uint8_t last_host_seq = 255;

/* ========= Timing ========= */
static uint32_t last_hb_ms = 0;
static uint32_t last_arr_ms = 0;
static uint32_t last_dl_ms = 0;

/* Forward declarations */
static uint8_t checksum_xor(const char *data);
static void send_packet_auto(const char *type, const char *node, const char *data);
static void send_packet_reply(const char *type, const char *node, uint8_t seq, const char *data);
static void handle_complete_message(const char *msg);

/**
 * @brief XOR checksum over ASCII payload bytes.
 * @param data Null-terminated payload string.
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
 * @brief Send a framed packet with auto-incrementing SEQ.
 *        Used for telemetry (HB/ARR/DL) and general messages not tied to a host command.
 */

static void send_packet_auto(const char *type, const char *node, const char *data)
{
    char payload[128];
    char frame[160];

    uint8_t seq = tx_seq++;  // Global sequence for every TX frame (telemetry etc.)

    // Build: TYPE|NODE|SEQ|DATA
    int n = snprintf(payload, sizeof(payload), "%s|%s|%u|%s", type, node, seq, data);
    if (n < 0 || n >= (int)sizeof(payload)) return;

    uint8_t chk = checksum_xor(payload);

    // Build: <STX>payload|CHK<ETX>
    n = snprintf(frame, sizeof(frame), "%c%s|%02X%c", STX, payload, chk, ETX);
    if (n < 0 || n >= (int)sizeof(frame)) return;

    HAL_UART_Transmit(&huart3, (uint8_t*)frame, (uint16_t)strlen(frame), HAL_MAX_DELAY);
}

/**
 * @brief Send a framed reply that echoes HOST SEQ.
 *        This is REQUIRED for host ACK/STATUS matching and retry logic.
 */
static void send_packet_reply(const char *type, const char *node, uint8_t seq, const char *data)
{
    char payload[128];
    char frame[160];

    int n = snprintf(payload, sizeof(payload), "%s|%s|%u|%s", type, node, seq, data);
    if (n < 0 || n >= (int)sizeof(payload)) return;

    uint8_t chk = checksum_xor(payload);

    n = snprintf(frame, sizeof(frame), "%c%s|%02X%c", STX, payload, chk, ETX);
    if (n < 0 || n >= (int)sizeof(frame)) return;

    HAL_UART_Transmit(&huart3, (uint8_t*)frame, (uint16_t)strlen(frame), HAL_MAX_DELAY);
}

/**
 * @brief Parse a complete message (without STX/ETX), validate checksum, and handle commands.
 * Expected message string format (without STX/ETX):
 *   TYPE|NODE|SEQ|DATA|CHK
 *
 * DATA may contain extra '|' characters, so we split checksum from the end, then parse the first fields.
 */

static void handle_complete_message(const char *msg)
{
    char copy[RX_BUFFER_SIZE];
    strncpy(copy, msg, sizeof(copy) - 1);
    copy[sizeof(copy) - 1] = '\0';

    // Split checksum from the end: "...|CHK"
    char *last_bar = strrchr(copy, '|');
    if (!last_bar) {
        send_packet_auto("ERR", NODE_ID, "FORMAT");
        return;
    }

    char *chk_str = last_bar + 1;
    *last_bar = '\0'; // now copy = "TYPE|NODE|SEQ|DATA"

    uint8_t calc_chk = checksum_xor(copy);
    uint8_t recv_chk = (uint8_t)strtoul(chk_str, NULL, 16);

    if (calc_chk != recv_chk) {
        send_packet_auto("ERR", NODE_ID, "CHK");
        return;
    }

    // Parse first fields: TYPE|NODE|SEQ|DATA(rest)
    char *type    = strtok(copy, "|");
    char *node    = strtok(NULL, "|");
    char *seq_str = strtok(NULL, "|");
    char *data    = strtok(NULL, ""); // remainder as DATA

    if (!type || !node || !seq_str || !data) {
        send_packet_auto("ERR", NODE_ID, "FORMAT");
        return;
    }

    uint8_t host_seq = (uint8_t)atoi(seq_str);

    // Duplicate detection for HOST commands (simple last-seq)
    if (strcmp(type, "CMD") == 0) {
        if (host_seq == last_host_seq) {
            // Optional improvement: re-send last reply.
            // For now, ignore duplicates safely.
            return;
        }
        last_host_seq = host_seq;
    }

    // Only accept commands from host
    if (strcmp(type, "CMD") == 0)
    {
        (void)node; // node is "HOST" typically; not required for this demo

        if (strcmp(data, "PING") == 0) {
            send_packet_reply("ACK", NODE_ID, host_seq, "PONG");
        }
        else if (strcmp(data, "STATUS") == 0) {
            char info[96];
            snprintf(info, sizeof(info), "NODE=%s,ROUTE=%s,ETA=%d", NODE_ID, ROUTE_ID, CURRENT_ETA);
            send_packet_reply("STATUS", NODE_ID, host_seq, info);
        }
        else if (strncmp(data, "SETROUTE=", 9) == 0) {
            strncpy(ROUTE_ID, data + 9, sizeof(ROUTE_ID) - 1);
            ROUTE_ID[sizeof(ROUTE_ID) - 1] = '\0';
            send_packet_reply("ACK", NODE_ID, host_seq, "ROUTE_SET");
        }
        else if (strncmp(data, "SETETA=", 7) == 0) {
            CURRENT_ETA = atoi(data + 7);
            send_packet_reply("ACK", NODE_ID, host_seq, "ETA_SET");
        }
        else {
            send_packet_reply("ERR", NODE_ID, host_seq, "UNKNOWN_CMD");
        }
    }
    else {
        // Ignore unknown types quietly OR respond with error (your choice)
        // send_packet_auto("ERR", NODE_ID, "UNKNOWN_TYPE");
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
          send_packet_auto("HB", NODE_ID, "OK");
      }

      /* Arrival update every 10 seconds */
      if ((t - last_arr_ms) >= 10000)
      {
          last_arr_ms = t;

          char data[96];
          snprintf(data, sizeof(data), "ROUTE=%s,STOP=STOP12,ETA=%d", ROUTE_ID, CURRENT_ETA);
          send_packet_auto("ARR", NODE_ID, data);
      }

      /* Delay event every 30 seconds */
      if ((t - last_dl_ms) >= 30000)
      {
          last_dl_ms = t;
          send_packet_auto("DL", NODE_ID, "+5MIN");
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
  * PB10 -> USART3_TX (AF7)
  * PB11 -> USART3_RX (AF7)
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
 * @brief UART RX complete callback (interrupt-driven).
 * Builds messages framed by STX/ETX into rx_buffer, then calls handle_complete_message().
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
                receiving = 0;
                rx_index = 0;
                send_packet_auto("ERR", NODE_ID, "RX_OVERFLOW");
            }
        }

        /* Re-arm RX interrupt */
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
