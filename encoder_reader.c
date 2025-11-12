// TVArgenta - encoder + LED de estado en GPIO25
// Compila con libgpiod 1.6.3: gcc -O2 -o encoder_reader encoder_reader.c -lgpiod
// LED ON mientras el proceso está vivo; OFF al salir (CTRL+C o shutdown).
// Wiring: LED -> GPIO25, otra pata -> GND.

#include <gpiod.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <signal.h>

#define CHIP "/dev/gpiochip0"
#define NEXT 3 
#define CLK  23
#define DT   17
#define SW   27
#define LED  25

static struct gpiod_line *next_btn = NULL;
static struct gpiod_chip *chip = NULL;
static struct gpiod_line *clk  = NULL;
static struct gpiod_line *dt   = NULL;
static struct gpiod_line *sw   = NULL;
static struct gpiod_line *led  = NULL;
static volatile sig_atomic_t running = 1;

static void cleanup(void) {
    // Apagar LED y soltar líneas al salir
    if (led) {
        // Ignorar errores si ya no está disponible
        gpiod_line_set_value(led, 0);
        gpiod_line_release(led);
        led = NULL;
    }
    if (clk)  { gpiod_line_release(clk);  clk  = NULL; }
    if (dt)   { gpiod_line_release(dt);   dt   = NULL; }
    if (sw)   { gpiod_line_release(sw);   sw   = NULL; }
    if (chip) { gpiod_chip_close(chip);   chip = NULL; }
	if (next_btn) { gpiod_line_release(next_btn); next_btn = NULL; }
}

static void on_signal(int sig) {
    (void)sig;
    running = 0;
}

int main(void) {
    // Señales para finalizar prolijo (apaga LED)
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = on_signal;
    sigaction(SIGINT,  &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);

    chip = gpiod_chip_open(CHIP);
    if (!chip) {
        perror("gpiod_chip_open");
        return 1;
    }

    clk = gpiod_chip_get_line(chip, CLK);
    dt  = gpiod_chip_get_line(chip, DT);
    sw  = gpiod_chip_get_line(chip, SW);
    led = gpiod_chip_get_line(chip, LED);
	next_btn = gpiod_chip_get_line(chip, NEXT);

	if (!next_btn) {
		perror("gpiod_chip_get_line (NEXT)");
		cleanup();
		return 1;
	}

    if (!clk || !dt || !sw || !led) {
        perror("gpiod_chip_get_line");
        cleanup();
        return 1;
    }

    // Inputs: CLK/DT sin bias explícito, SW con pull-up
    struct gpiod_line_request_config in_cfg = {
        .consumer = "encoder",
        .request_type = GPIOD_LINE_REQUEST_DIRECTION_INPUT,
        .flags = 0
    };
    if (gpiod_line_request(clk, &in_cfg, 0) < 0 ||
        gpiod_line_request(dt,  &in_cfg, 0) < 0) {
        perror("line_request_input (clk/dt)");
        cleanup();
        return 1;
    }

    in_cfg.flags = GPIOD_LINE_REQUEST_FLAG_BIAS_PULL_UP;
    if (gpiod_line_request(sw, &in_cfg, 0) < 0) {
        perror("line_request_input (sw pull-up)");
        cleanup();
        return 1;
    }
	
	in_cfg.flags = GPIOD_LINE_REQUEST_FLAG_BIAS_PULL_UP;
	if (gpiod_line_request(next_btn, &in_cfg, 0) < 0) {
		perror("line_request_input (next_btn pull-up)");
		cleanup();
		return 1;
	}

    // Output: LED en alto (encendido) mientras corra el proceso
    struct gpiod_line_request_config out_cfg = {
        .consumer = "tvargenta-led",
        .request_type = GPIOD_LINE_REQUEST_DIRECTION_OUTPUT,
        .flags = 0
    };
    if (gpiod_line_request(led, &out_cfg, 1) < 0) {  // default_val = 1 (ON)
        perror("line_request_output (led)");
        cleanup();
        return 1;
    }
    // Redundante pero explícito:
    gpiod_line_set_value(led, 1);

    int last_clk = gpiod_line_get_value(clk);
    int last_sw  = gpiod_line_get_value(sw);
    int sw_pressed = 0;
    int sw_released = 0;
	int last_next = gpiod_line_get_value(next_btn);
	struct timespec ts_now;
	double last_next_fire = 0.0;         // último disparo BTN_NEXT (segundos)
	const double NEXT_DEBOUNCE = 1.0;    // 1 segundo de antibounce

    // Loop principal: emite ROTARY y BTN_* por stdout (como ya usás)
    while (running) {
        int clk_val = gpiod_line_get_value(clk);
        int dt_val  = gpiod_line_get_value(dt);
        int sw_val  = gpiod_line_get_value(sw);

        // ROTARY
        if (clk_val != last_clk) {
            if (clk_val == 0) { // flanco descendente
                if (dt_val != clk_val)
                    printf("ROTARY_CW\n");
                else
                    printf("ROTARY_CCW\n");
                fflush(stdout);
            }
            last_clk = clk_val;
        }

        // BOTÓN
        if (sw_val != last_sw) {
            if (sw_val == 0 && !sw_pressed) {
                printf("BTN_PRESS\n");
                fflush(stdout);
                sw_pressed = 1;
                sw_released = 0;
            } else if (sw_val == 1 && !sw_released && sw_pressed) {
                printf("BTN_RELEASE\n");
                fflush(stdout);
                sw_pressed = 0;
                sw_released = 1;
            }
            last_sw = sw_val;
        }
		
		// --- BOTÓN NEXT en GPIO3 (activo en 0, pull-up) con antirrebote de 1s ---
		int next_val = gpiod_line_get_value(next_btn);
		if (next_val != last_next) {
			// Flanco de bajada = PRESIONADO (activo-bajo)
			if (next_val == 0) {
				// Tiempo actual en segundos
				clock_gettime(CLOCK_MONOTONIC, &ts_now);
				double now_s = ts_now.tv_sec + ts_now.tv_nsec / 1e9;

				if ((now_s - last_next_fire) >= NEXT_DEBOUNCE) {
					printf("BTN_NEXT\n");
					fflush(stdout);
					last_next_fire = now_s;
				}
			}
			last_next = next_val;
		}
	

        usleep(3000);  // 3 ms
    }

    // Al salir por señal o fin: apagar LED
    cleanup();
    return 0;
}
