"""
Map XEMA variables to meteo columns.
"""

xema_namings = {
    1: "Px",
    2: "Pn",
    3: "HRx",
    30: "VV10",
    31: "DV10",
    32: "T",
    33: "HR",
    34: "P",
    35: "PPT",
    36: "RS",
    40: "Tx",
    42: "Tn",
    44: "HRn",
    50: "VVx10",
    51: "DVVx10",
    72: "PPTx1min"
}


xema_meteo_mappings = {
    "TA_Avg": "XEMA_T",
    "RH_Avg": "XEMA_HR",
    "PA": "XEMA_P",
    "PRECIP_Tot": "XEMA_PPT",
    "PAR_1_Avg": "XEMA_RS",
    "SW_IN_Avg": "XEMA_RS",
}
