cmake_minimum_required(VERSION 3.15)
project(Moray LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ── pybind11 (header-only, fetched automatically) ────────────────────
find_package(pybind11 CONFIG REQUIRED)

# ── Extension module ─────────────────────────────────────────────────
pybind11_add_module(moray_core
    src/engine/_cpp/main_bindings.cpp
    src/engine/_cpp/board/board.cpp
    src/engine/_cpp/board/bindings.cpp
    src/engine/_cpp/move_generation/move_generation.cpp
    src/engine/_cpp/move_generation/bindings.cpp
    src/engine/_cpp/search/search.cpp
    src/engine/_cpp/search/zobrist.cpp
    src/engine/_cpp/search/transposition_table.cpp
    src/engine/_cpp/search/static_exchange.cpp
    src/engine/_cpp/search/move_sorter.cpp
    src/engine/_cpp/search/minimax.cpp
    src/engine/_cpp/search/bindings.cpp
    src/engine/_cpp/extractors/extractors.cpp
    src/engine/_cpp/extractors/bindings.cpp
    src/engine/_cpp/pgn/pgn.cpp
    src/engine/_cpp/pgn/bindings.cpp
    src/engine/_cpp/evaluators/evaluators.cpp
    src/engine/_cpp/evaluators/eval_bindings.cpp
)

target_include_directories(moray_core PRIVATE
    ${CMAKE_SOURCE_DIR}/src/engine/_core
    ${CMAKE_SOURCE_DIR}/src/engine/_cpp
    ${CMAKE_SOURCE_DIR}/src/engine/_cpp/board
    ${CMAKE_SOURCE_DIR}/src/engine/_cpp/move_generation
    ${CMAKE_SOURCE_DIR}/src/engine/_cpp/search
    ${CMAKE_SOURCE_DIR}/src/engine/_cpp/extractors
    ${CMAKE_SOURCE_DIR}/src/engine/_cpp/pgn
    ${CMAKE_SOURCE_DIR}/src/engine/_cpp/evaluators
)

target_compile_definitions(moray_core PRIVATE
    VERSION_INFO="dev"
    NDEBUG
)

# Release-mode flags (scikit-build-core sets CMAKE_BUILD_TYPE=Release)
if(NOT MSVC)
    target_compile_options(moray_core PRIVATE
        -O3
        -march=native
        -mtune=native
        -ffast-math
        # Search windows intentionally use IEEE +/-infinity sentinels, and
        # configuration validation must distinguish infinity and NaN.
        -fno-finite-math-only
        -funroll-loops
        -finline-functions
        -flto
        -Wall
        -Wextra
    )
    target_link_options(moray_core PRIVATE -flto -O3)
else()
    target_compile_options(moray_core PRIVATE /O2 /W3 /GL)
    target_link_options(moray_core PRIVATE /LTCG)
endif()

# ── Place .so directly in source tree (needed for editable installs) ──
# Editable (inplace) builds don't run cmake --install, so we force the
# output directory so the .so lands where Python can find it.
set_target_properties(moray_core PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/src/engine/_core"
)

# For wheel builds (non-editable), scikit-build-core uses cmake --install.
install(TARGETS moray_core
    DESTINATION engine/_core
)
