import streamlit as st


def apply_app_style():
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1200px;
            padding-top: 4rem;
            padding-bottom: 4rem;
        }

        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(128, 128, 128, 0.18);
        }

        div[data-testid="stMetric"] {
            border: 1px solid rgba(128, 128, 128, 0.18);
            border-radius: 18px;
            padding: 16px;
            background: rgba(255, 255, 255, 0.025);
        }

        .hero-card {
            margin-top: 0.5rem;
            padding: 3rem;
            margin-bottom: 2.5rem;

            border: 1px solid rgba(134, 239, 172, 0.25);
            border-radius: 28px;

            background:
                radial-gradient(circle at top right,
                rgba(134,239,172,0.16), transparent 35%),
                radial-gradient(circle at bottom left,
                rgba(244,114,182,0.12), transparent 40%);
        }

        .hero-card h1 {
            margin: 0 0 0.4rem 0;
            font-size: 2.25rem;
        }

        .hero-card p {
            margin: 0;
            opacity: 0.82;
            font-size: 1.05rem;
            line-height: 1.8;
        }

        .feature-card {
            min-height: 170px;
            padding: 1.4rem;
            border: 1px solid rgba(128, 128, 128, 0.18);
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.025);
        }

        .feature-card h3 {
            margin: 0 0 0.8rem 0;
            font-size: 1.45rem;
            line-height: 1.35;
            white-space: nowrap;
        }

        .feature-card p {
            margin: 0;
            opacity: 0.74;
            line-height: 1.65;
        }

        .start-card {
            margin-top: 2rem;
            padding: 18px 22px;

            border-radius: 18px;

            border: 1px solid rgba(59,130,246,.25);

            background: rgba(59,130,246,.12);

            color: #dbeafe;

            font-size: 1rem;
        }

        .coming-soon {
            max-width: 720px;
            margin: 3rem auto;
            padding: 3rem 2rem;
            text-align: center;
            border: 1px dashed rgba(128, 128, 128, 0.35);
            border-radius: 24px;
        }

        .coming-icon {
            font-size: 3rem;
            margin-bottom: 0.8rem;
        }

        .security-note {
            padding: 1rem 1.2rem;
            border-radius: 16px;
            background: rgba(96, 165, 250, 0.10);
            border: 1px solid rgba(96, 165, 250, 0.20);
        }

        @media (max-width: 768px) {
            .block-container {
                padding-top: 2rem;
            }

            .hero-card {
                padding: 1.4rem;
            }

            .hero-card h1 {
                font-size: 1.75rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
