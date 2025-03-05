import streamlit as st
import streamlit_shadcn_ui as shadcn

def main():
    # Set page title and overall styling
    st.set_page_config(page_title="BACflow - Home", layout="wide")
    st.markdown(
        """
        <style>
        .hero {
            text-align: center;
            padding: 3rem 0;
            background-color: #f0f4f8;
        }
        .hero h1 {
            font-size: 3.5rem;
            color: #4A90E2;
            margin-bottom: 0.5rem;
        }
        .hero h3 {
            font-size: 1.75rem;
            color: #333;
            margin-bottom: 2rem;
        }
        .section-header {
            margin-top: 3rem;
            margin-bottom: 1rem;
        }
        .pricing-table {
            width: 100%;
            border-collapse: collapse;
        }
        .pricing-table th, .pricing-table td {
            border: 1px solid #ddd;
            padding: 0.75rem;
            text-align: center;
        }
        .pricing-table th {
            background-color: #4A90E2;
            color: #fff;
        }
        .faq-question {
            font-weight: bold;
            margin-top: 1rem;
        }
        .faq-answer {
            margin-bottom: 1rem;
        }
        </style>
        """, unsafe_allow_html=True
    )

    # ---------------- Hero Section ----------------
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.markdown("<h1>BACflow</h1>", unsafe_allow_html=True)
    st.markdown("<h3>The Future of Blood Alcohol Estimation</h3>", unsafe_allow_html=True)
    st.image("https://via.placeholder.com/1200x400.png?text=Your+Hero+Image+Here", use_column_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- Features Overview ----------------
    st.markdown('<h2 class="section-header">Features Overview</h2>', unsafe_allow_html=True)
    st.markdown(
        """
        - **Dynamic Absorption Modeling:** Incorporates food intake data to adjust alcohol absorption dynamically.
        - **Accurate Simulation:** High-fidelity BAC simulation using multiple models and elimination kinetics.
        - **Threshold Detection:** Automatically identifies driving safe and sober times.
        - **Modern & Intuitive UI:** Built with Streamlit and shadcn UI components for a delightful experience.
        - **Secure Data Management:** User data stored safely in a local SQLite database.
        """, unsafe_allow_html=True
    )

    # ---------------- Pricing Table ----------------
    st.markdown('<h2 class="section-header">Pricing</h2>', unsafe_allow_html=True)
    st.markdown(
        """
        <table class="pricing-table">
            <thead>
                <tr>
                    <th>Plan</th>
                    <th>Features</th>
                    <th>Price/month</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Free</strong></td>
                    <td>Basic BAC estimation, single model simulation</td>
                    <td>$0</td>
                </tr>
                <tr>
                    <td><strong>Pro</strong></td>
                    <td>Multi-model simulation, historical data management, alerts</td>
                    <td>$9.99</td>
                </tr>
                <tr>
                    <td><strong>Enterprise</strong></td>
                    <td>Custom integrations, advanced analytics, dedicated support</td>
                    <td>Contact Us</td>
                </tr>
            </tbody>
        </table>
        """, unsafe_allow_html=True
    )

    # ---------------- FAQ Section ----------------
    st.markdown('<h2 class="section-header">Frequently Asked Questions</h2>', unsafe_allow_html=True)
    faqs = [
        {
            "question": "How accurate is BACflow?",
            "answer": "BACflow leverages advanced simulation models based on validated research. It is designed for informational purposes only."
        },
        {
            "question": "Can I use BACflow for legal decisions?",
            "answer": "No. BACflow is for entertainment and research purposes only. Please consult legal and medical professionals for advice."
        },
        {
            "question": "How is my data stored?",
            "answer": "All user data is securely stored in a local SQLite database and is not shared without your consent."
        },
        {
            "question": "What support is available?",
            "answer": "Please use the contact form below for any inquiries or support requests."
        },
    ]
    for faq in faqs:
        st.markdown(f"<div class='faq-question'>Q: {faq['question']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='faq-answer'>A: {faq['answer']}</div>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

    # ---------------- Contact Form ----------------
    st.markdown('<h2 class="section-header">Contact Us</h2>', unsafe_allow_html=True)
    with st.form("contact_form"):
        name = shadcn.TextInput(label="Your Name", placeholder="Enter your name")
        email = shadcn.TextInput(label="Email", placeholder="Enter your email")
        message = shadcn.TextArea(label="Message", placeholder="Enter your message", height=150)
        submitted = st.form_submit_button("Send Message")
        if submitted:
            st.success("Thank you for reaching out! We'll get back to you soon.")
            # Implement sending email or storing the message as needed.

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>© 2024 BACflow. All rights reserved.</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
