#Summary cards
        cards_layout = QHBoxLayout()

        #first
        total_scans_card = QFrame()

        #CSS Size
        total_scans_card.setFixedSize(200, 120)

        total_scans_card.setObjectName("total_scans_card")

        total_scans_layout = QVBoxLayout()
        total_scans_card.setLayout(total_scans_layout)

        # CSSS**
        total_scans_card.setStyleSheet("""
            #total_scans_card {
                border: 2px solid black;
                border-radius: 10px;
            }
        """)

        total_scans_title = QLabel("Total Scans")
        total_scans_number = QLabel("12")

        #CSS***
        total_scans_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        total_scans_number.setAlignment(Qt.AlignmentFlag.AlignCenter)

        total_scans_layout.addWidget(total_scans_title)
        total_scans_layout.addWidget(total_scans_number)

        cards_layout.addWidget(total_scans_card)

        content_layout.addLayout(cards_layout)