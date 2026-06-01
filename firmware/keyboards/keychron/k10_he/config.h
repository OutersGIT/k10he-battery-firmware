/* Copyright 2025 @ Keychron (https://www.keychron.com)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#pragma once

/*
 * Only the battery-mod additions are shown here. Merge this define into the
 * stock keychron/k10_he/config.h (do NOT replace the whole file): the rest of
 * the keyboard configuration is unchanged.
 *
 * Model identifier reported in KC_GET_BATTERY (data[6]) so the host can show
 * the keyboard model even over the 2.4 GHz dongle. It must live in config.h
 * (not a .c file) so every translation unit, including the shared
 * keychron_raw_hid.c, sees the same value.
 */
#define KC_BATTERY_MODEL_ID 1
