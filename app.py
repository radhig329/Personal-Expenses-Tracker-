import matplotlib.pyplot as plt
import streamlit as st
import sqlite3
import pandas as pd


st.set_page_config(
    page_title="Personal Expenses Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main {
        background-color: #f5f7fb;
    }

    h1 {
        color: #17365D;
        font-weight: 700;
    }

    h2, h3 {
        color: #24476B;
    }

    div[data-testid="stMetric"] {
    background-color: white;
    color: #17365D;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    }

    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #17365D !important;
    }

    div.stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)



# Connect to database
conn = sqlite3.connect("expenses.db", check_same_thread=False)

# Create table if it does not exist
conn.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        description TEXT
    )
""")
conn.commit()

# Add date column if it does not exist
columns = [
    row[1] for row in conn.execute(
        "PRAGMA table_info(expenses)"
    ).fetchall()
]

if "expense_date" not in columns:
    conn.execute(
        "ALTER TABLE expenses ADD COLUMN expense_date TEXT"
    )
    conn.commit()


st.title("💰 Personal Expenses Tracker")
st.sidebar.title("💰 Expense Tracker")

menu = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Add Expense",
        "Expense History",
        "Edit Expense",
        "Budget",
        "Search & Filters",
        "Analytics"
    ]
)
st.write("Manage your daily expenses easily.")
if menu == "Add Expense":
# Add expense form
    st.subheader("Add a New Expense")

    with st.form("expense_form"):
        amount = st.number_input(
            "Enter Amount (₹)",
            min_value=1.0,
            step=10.0
        )

        category = st.selectbox(
            "Select Category",
            ["Food", "Travel", "Shopping", "Bills", "Education", "Other"]
        )

        description = st.text_input("Description")
        expense_date = st.date_input("Expense Date")

        

        submitted = st.form_submit_button("Add Expense")

        if submitted:
        
            conn.execute(
                "INSERT INTO expenses (amount, category, description, expense_date) VALUES (?, ?, ?, ?)",
                (amount, category, description, expense_date.isoformat())
        )

            conn.commit()
            st.success("Expense saved successfully!")
            st.rerun()

# Read expenses from database
df = pd.read_sql_query(
    "SELECT id, amount, category, description, expense_date FROM expenses ORDER BY id DESC",
    conn
)
df["expense_date"] = pd.to_datetime(
    df["expense_date"], errors="coerce"
)


# Monthly Budget Management
if menu == "Budget":
    st.subheader("💰 Monthly Budget")

    monthly_budget = st.number_input(
        "Set Your Monthly Budget (₹)",
        min_value=0.0,
        value=10000.0,
        step=500.0,
        key="monthly_budget"
    )


    # Monthly Expense Filter
    st.subheader("📅 Monthly Expense Filter")

    # Calculate Monthly Spending
    current_month = pd.Timestamp.today().strftime("%Y-%m")

    current_month_df = df[
        df["expense_date"].dt.strftime("%Y-%m") == current_month
    ]

    monthly_spending = current_month_df["amount"].sum()

    remaining_budget = monthly_budget - monthly_spending

    # Budget Usage Progress
    if monthly_budget > 0:
        budget_used = monthly_spending / monthly_budget
        progress = min(budget_used, 1.0)

        st.write("Monthly Budget Usage")
        st.progress(progress)

        st.caption(f"{budget_used * 100:.1f}% of your budget used")


    # Budget Warning
    if remaining_budget < 0:
        st.error(
            f"⚠️ Budget Exceeded! You spent ₹{abs(remaining_budget):,.2f} more than your budget."
        )
    elif remaining_budget == 0:
        st.warning("You have used your entire monthly budget!")
    else:
        st.success("You are within your monthly budget!")

    col1, col2 = st.columns(2)

    col1.metric(
        "Monthly Spending",
        f"₹{monthly_spending:,.2f}"
    )

    col2.metric(
        "Remaining Budget",
        f"₹{remaining_budget:,.2f}"
    )

    if not df.empty:
        df["expense_date"] = pd.to_datetime(
            df["expense_date"], errors="coerce"
        )

        valid_dates = df.dropna(subset=["expense_date"])

        if not valid_dates.empty:
            available_months = (
                valid_dates["expense_date"]
                .dt.to_period("M")
                .astype(str)
                .unique()
                .tolist()
            )

            selected_month = st.selectbox(
                "Select Month",
                available_months
            )

            monthly_df = valid_dates[
                valid_dates["expense_date"].dt.to_period("M").astype(str)
                == selected_month
            ]

            st.metric(
                "Expenses This Month",
                f"₹{monthly_df['amount'].sum():,.2f}"
            )

            st.dataframe(
                monthly_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Add a new expense with a date to use this filter.")
    else:
        st.info("No expenses available yet.")
    
    # Dashboard
if menu == "Dashboard":
    st.subheader("Expense Dashboard")

    total_expenses = df["amount"].sum() if not df.empty else 0
    expense_count = len(df)

    col1, col2 = st.columns(2)

    col1.metric("Total Expenses", f"₹{total_expenses:,.2f}")
    col2.metric("Number of Expenses", expense_count)


    # Edit Expense
if menu == "Edit Expense":
    st.subheader("✏️ Edit an Expense")

    if not df.empty:
        selected_id = st.selectbox(
            
            "Select Expense ID to Edit",
            df["id"].tolist(),
            key="edit_expense_id"
        )

        selected_expense = df[df["id"] == selected_id].iloc[0]

        with st.form("edit_expense_form"):
            new_amount = st.number_input(
                "Update Amount (₹)",
                min_value=1.0,
                value=float(selected_expense["amount"])
            )

            categories = [
                "Food", "Travel", "Shopping",
                "Bills", "Education", "Other"
            ]

            current_category = selected_expense["category"]
            category_index = (
                categories.index(current_category)
                if current_category in categories else 0
            )

            new_category = st.selectbox(
                "Update Category",
                categories,
                index=category_index
            )

            new_description = st.text_input(
                "Update Description",
                value=str(selected_expense["description"] or "")
            )

            new_date = st.date_input(
                "Update Expense Date",
                value=(
                    selected_expense["expense_date"].date()
                    if pd.notna(selected_expense["expense_date"])
                    else pd.Timestamp.today().date()
                )
                    
            )

            update_button = st.form_submit_button("Update Expense")

            if update_button:
                edit_conn = sqlite3.connect("expenses.db")
                edit_conn.execute(

                     """UPDATE expenses
                    SET amount = ?, category = ?, description = ?, expense_date = ?
                    WHERE id = ?""",
                    (new_amount, new_category, new_description, new_date.isoformat(), selected_id)
                )

                edit_conn.commit()
                edit_conn.close()

                st.success("Expense updated successfully!")
                st.rerun()
            else:
             st.info("No expenses available to edit.")

    # Search Expenses
if menu == "Search & Filters":
    st.subheader("🔍 Search Expenses")

    search_query = st.text_input(
        "Search by category or description"
    )

    if search_query:
        search_df = df[
            df["category"].str.contains(
                search_query, case=False, na=False
            )
            |
            df["description"].str.contains(
                search_query, case=False, na=False
            )
        ]

        st.dataframe(
            search_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.caption("Enter a category or description to search.")

    # Date Range Filter
    st.subheader("📅 Filter Expenses by Date Range")

    date_range = st.date_input(
        "Select Date Range",
        value=(),
        key="date_range_filter"
    )

    if len(date_range) == 2:
        start_date, end_date = date_range

        filtered_df = df[
            df["expense_date"].notna()
            & (df["expense_date"] >= pd.Timestamp(start_date))
            & (df["expense_date"] < pd.Timestamp(end_date) + pd.Timedelta(days=1))
        ]

        st.write("Filtered Expenses:")
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total in Selected Range",
            f"₹{filtered_df['amount'].sum():,.2f}"
        )
    else:
        st.caption("Select a start date and end date to filter expenses.")
if menu == "Expense History":
# Expense history
    st.subheader("Expense History")

    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No expenses added yet.")


    # Delete Expense
    st.subheader("Delete an Expense")

    if not df.empty:
        expense_id = st.selectbox(
            "Select Expense ID to Delete",
            df["id"].tolist()
        )

        if st.button("Delete Expense"):
            conn = sqlite3.connect("expenses.db", check_same_thread=False)
            conn.execute(
                "DELETE FROM expenses WHERE id = ?",
                (expense_id,)
            )
            conn.commit()
            conn.close()

            st.success("Expense deleted successfully!")
            st.rerun()
    else:
        st.info("No expenses available to delete.")

# Expense Category Chart
if menu == "Analytics":
    st.title("📊 Analytics Dashboard")
    
    st.subheader("📊 Expenses by Category")

    if not df.empty:
        category_expenses = df.groupby("category")["amount"].sum()

        st.write("Category-wise spending:")
        st.bar_chart(category_expenses)
    else:
        st.info("Add some expenses to see the chart.")

    # Pie Chart Analytics
    st.subheader("🥧 Category-wise Expense Distribution")

    if not df.empty:
        pie_data = df.groupby("category")["amount"].sum()

        st.write("Spending distribution by category:")

        fig, ax = plt.subplots(figsize=(7, 7))

        pie_data.plot.pie(

            autopct="%1.1f%%",
            ax=ax,
            ylabel=""
       )

        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("Add expenses to see the pie chart.")

# Close database connection
conn.close()