class StrategyTakeProfit:
    PRESET_EQUAL_DISTRIBUTION_LABEL = 'equal_distribution'
    PRESET_GREEDY_LOW_LABEL = 'greedy_low'
    PRESET_GREEDY_LOW_MEDIUM_LABEL = 'greedy_low_medium'
    PRESET_GREEDY_MEDIUM_LABEL = 'greedy_medium'
    PRESET_GREEDY_HIGH_LABEL = 'greedy_high'

    PRESET_EQUAL_DISTRIBUTION = {
        1: {
            1: 1
        },
        2: {
            1: 1/2,
            2: 1/2,
        },
        3: {
            1: 1/3,
            2: 1/3,
            3: 1/3,
        },
        4: {
            1: 1/4,
            2: 1/4,
            3: 1/4,
            4: 1/4,
        },
        5: {
            1: 1/5,
            2: 1/5,
            3: 1/5,
            4: 1/5,
            5: 1/5,
        }
    }

    PRESET_GREEDY_LOW = {
        1: {
            1: 1
        },
        2: {
            1: 1,
            2: 0
        },
        3: {
            1: 1,
            2: 0,
            3: 0,
        },
        4: {
            1: 1,
            2: 0,
            3: 0,
            4: 0
        },
        5: {
            1: 1,
            2: 0,
            3: 0,
            4: 0,
            5: 0
        },
    }

    PRESET_GREEDY_LOW_MEDIUM = {
        1: {
            1: 1
        },
        2: {
            1: 3/4,
            2: 1/4
        },
        3: {
            1: 2/3,
            2: 1/3,
            3: 0,
        },
        4: {
            1: 2/3,
            2: 1/3,
            3: 0,
            4: 0
        },
        5: {
            1: 2/3,
            2: 1/3,
            3: 0,
            4: 0,
            5: 0
        },
    }

    PRESET_GREEDY_MEDIUM = {
        1: {
            1: 1
        },
        2: {
            1: 2/3,
            2: 1/3
        },
        3: {
            1: 3/6,
            2: 2/6,
            3: 1/6
        },
        4: {
            1: 5/10,
            2: 3/10,
            3: 2/10,
            4: 1/10
        },
        5: {
            1: 4/10,
            2: 3/10,
            3: 2/10,
            4: 1/10,
            5: 1/10
        }
    }

    PRESET_GREEDY_HIGH = {
        1: {
            1: 1
        },
        2: {
            1: 1/3,
            2: 2/3
        },
        3: {
            1: 1/6,
            2: 2/6,
            3: 3/6
        },
        4: {
            1: 1/10,
            2: 2/10,
            3: 3/10,
            4: 5/10,
        },
        5: {
            1: 1/10,
            2: 1/10,
            3: 2/10,
            4: 3/10,
            5: 3/10,
        }
    }

    choices = (
        (PRESET_EQUAL_DISTRIBUTION_LABEL, PRESET_EQUAL_DISTRIBUTION),
        (PRESET_GREEDY_LOW_LABEL, PRESET_GREEDY_LOW),
        (PRESET_GREEDY_LOW_MEDIUM_LABEL, PRESET_GREEDY_LOW_MEDIUM),
        (PRESET_GREEDY_MEDIUM_LABEL, PRESET_GREEDY_MEDIUM),
        (PRESET_GREEDY_HIGH_LABEL, PRESET_GREEDY_HIGH),
    )
    mapping = {
        PRESET_EQUAL_DISTRIBUTION_LABEL: PRESET_EQUAL_DISTRIBUTION,
        PRESET_GREEDY_LOW_LABEL: PRESET_GREEDY_LOW,
        PRESET_GREEDY_LOW_MEDIUM_LABEL: PRESET_GREEDY_LOW_MEDIUM,
        PRESET_GREEDY_MEDIUM_LABEL: PRESET_GREEDY_MEDIUM,
        PRESET_GREEDY_HIGH_LABEL: PRESET_GREEDY_HIGH,
    }