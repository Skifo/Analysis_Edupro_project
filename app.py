import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

 
# Page configuration

st.set_page_config(
    page_title="EduPro Learner Analytics",
    
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = "EduPro_Online_Platform.xlsx"
AGE_BANDS = [0, 18, 26, 36, 46, 200]
AGE_LABELS = ["<18", "18-25", "26-35", "36-45", "45+"]

 
# Data loading & integration
 
@st.cache_data
def load_data(path: str):
    users = pd.read_excel(path, sheet_name="Users")
    courses = pd.read_excel(path, sheet_name="Courses")
    transactions = pd.read_excel(path, sheet_name="Transactions")

    # Referential integrity checks
    valid_users = transactions["UserID"].isin(users["UserID"])
    valid_courses = transactions["CourseID"].isin(courses["CourseID"])
    transactions = transactions[valid_users & valid_courses].copy()

    # Join: Transactions -> Users -> Courses
    df = transactions.merge(users, on="UserID", how="left")
    df = df.merge(courses, on="CourseID", how="left")

    # Age banding
    df["AgeGroup"] = pd.cut(df["Age"], bins=AGE_BANDS, labels=AGE_LABELS, right=False)
    users["AgeGroup"] = pd.cut(users["Age"], bins=AGE_BANDS, labels=AGE_LABELS, right=False)

    df["TransactionDate"] = pd.to_datetime(df["TransactionDate"])
    return users, courses, transactions, df


users_df, courses_df, transactions_df, full_df = load_data(DATA_PATH)

 
# Sidebar filters
 
st.sidebar.title(" EduPro Filters")
st.sidebar.caption("Slice the data to explore specific learner segments.")

age_options = [a for a in AGE_LABELS if a in full_df["AgeGroup"].unique().astype(str)]
selected_ages = st.sidebar.multiselect("Age Group", age_options, default=age_options)

gender_options = sorted(full_df["Gender"].dropna().unique().tolist())
selected_genders = st.sidebar.multiselect("Gender", gender_options, default=gender_options)

category_options = sorted(full_df["CourseCategory"].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect("Course Category", category_options, default=category_options)

level_options = ["Beginner", "Intermediate", "Advanced"]
level_options = [l for l in level_options if l in full_df["CourseLevel"].unique()]
selected_levels = st.sidebar.multiselect("Course Level", level_options, default=level_options)

type_options = sorted(full_df["CourseType"].dropna().unique().tolist())
selected_types = st.sidebar.multiselect("Course Type (Paid/Free)", type_options, default=type_options)

date_min = full_df["TransactionDate"].min().date()
date_max = full_df["TransactionDate"].max().date()
date_range = st.sidebar.date_input("Transaction Date Range", (date_min, date_max), min_value=date_min, max_value=date_max)

st.sidebar.markdown("---")
st.sidebar.caption("Data: Users, Courses & Transactions sheets, joined on UserID and CourseID.")

# Apply filters
mask = (
    full_df["AgeGroup"].astype(str).isin(selected_ages)
    & full_df["Gender"].isin(selected_genders)
    & full_df["CourseCategory"].isin(selected_categories)
    & full_df["CourseLevel"].isin(selected_levels)
    & full_df["CourseType"].isin(selected_types)
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
    mask &= (full_df["TransactionDate"].dt.date >= start) & (full_df["TransactionDate"].dt.date <= end)

fdf = full_df[mask].copy()

 
# Header & KPI row
 
st.title(" EduPro Learner Analytics Dashboard")
st.markdown(
    "Answering: *which age groups are most active, how enrollment differs by gender, "
    "which course categories are preferred by which segments, and whether beginner/"
    "intermediate/advanced courses skew toward specific age groups.*"
)

if fdf.empty:
    st.warning("No data matches the current filter selection. Please broaden your filters.")
    st.stop()

total_enrollments = len(fdf)
active_learners = fdf["UserID"].nunique()
avg_courses_per_learner = total_enrollments / active_learners if active_learners else 0
gender_ratio = fdf["Gender"].value_counts(normalize=True).mul(100).round(1)
top_category = fdf["CourseCategory"].value_counts().idxmax()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Enrollments", f"{total_enrollments:,}")
k2.metric("Active Learners", f"{active_learners:,}")
k3.metric("Avg Courses / Learner", f"{avg_courses_per_learner:.2f}")
k4.metric("Top Course Category", top_category)
gender_str = " / ".join([f"{g}: {p}%" for g, p in gender_ratio.items()])
k5.metric("Gender Split", gender_str)

st.markdown("---")

 
# Tabs for organized modules
 
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        " Demographic Overview",
        " Age-wise Enrollment",
        " Gender Preferences",
        " Category Popularity",
        " Segment Deep-Dive",
    ]
)

# --- Tab 1: Demographic overview  
with tab1:
    st.subheader("Learner Demographic Overview")
    c1, c2 = st.columns(2)

    with c1:
        age_dist = users_df[users_df["UserID"].isin(fdf["UserID"])]["AgeGroup"].value_counts().reindex(AGE_LABELS).fillna(0)
        fig = px.bar(
            x=age_dist.index.astype(str), y=age_dist.values,
            labels={"x": "Age Group", "y": "Number of Learners"},
            title="Learner Count by Age Group",
            color=age_dist.values, color_continuous_scale="Blues", text=age_dist.values,
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        gender_dist = users_df[users_df["UserID"].isin(fdf["UserID"])]["Gender"].value_counts()
        fig = px.pie(
            names=gender_dist.index, values=gender_dist.values,
            title="Gender Distribution of Active Learners", hole=0.45,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Age Distribution (Detailed Histogram)")
    fig = px.histogram(
        users_df[users_df["UserID"].isin(fdf["UserID"])], x="Age", nbins=20,
        color="Gender", barmode="overlay", opacity=0.7,
        title="Age Histogram by Gender",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Participation Level per Demographic Group")
    participation = (
        fdf.groupby(["AgeGroup", "Gender"], observed=True)["TransactionID"]
        .count().reset_index().rename(columns={"TransactionID": "Enrollments"})
    )
    fig = px.bar(
        participation, x="AgeGroup", y="Enrollments", color="Gender",
        barmode="group", title="Enrollments by Age Group and Gender",
        category_orders={"AgeGroup": AGE_LABELS},
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Tab 2: Age-wise enrollment  --
with tab2:
    st.subheader("Age-wise Enrollment Patterns")

    c1, c2 = st.columns(2)
    with c1:
        age_level = fdf.groupby(["AgeGroup", "CourseLevel"], observed=True).size().reset_index(name="Enrollments")
        fig = px.bar(
            age_level, x="AgeGroup", y="Enrollments", color="CourseLevel",
            barmode="stack", title="Course Level Preference by Age Group",
            category_orders={"AgeGroup": AGE_LABELS, "CourseLevel": ["Beginner", "Intermediate", "Advanced"]},
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        age_type = fdf.groupby(["AgeGroup", "CourseType"], observed=True).size().reset_index(name="Enrollments")
        fig = px.bar(
            age_type, x="AgeGroup", y="Enrollments", color="CourseType",
            barmode="group", title="Paid vs Free Course Uptake by Age Group",
            category_orders={"AgeGroup": AGE_LABELS},
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Age Group vs Course Category Heatmap")
    heat_data = pd.crosstab(fdf["AgeGroup"], fdf["CourseCategory"])
    heat_data = heat_data.reindex(AGE_LABELS)
    fig = px.imshow(
        heat_data, text_auto=True, aspect="auto", color_continuous_scale="YlGnBu",
        labels=dict(x="Course Category", y="Age Group", color="Enrollments"),
        title="Enrollment Intensity: Age Group vs Course Category",
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Tab 3: Gender preferences  ----
with tab3:
    st.subheader("Gender-Based Course Preference Analysis")

    c1, c2 = st.columns(2)
    with c1:
        gender_category = fdf.groupby(["Gender", "CourseCategory"], observed=True).size().reset_index(name="Enrollments")
        fig = px.bar(
            gender_category, x="CourseCategory", y="Enrollments", color="Gender",
            barmode="group", title="Course Category Preference by Gender",
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        gender_level = fdf.groupby(["Gender", "CourseLevel"], observed=True).size().reset_index(name="Enrollments")
        fig = px.bar(
            gender_level, x="CourseLevel", y="Enrollments", color="Gender",
            barmode="group", title="Course Level Comparison by Gender",
            category_orders={"CourseLevel": ["Beginner", "Intermediate", "Advanced"]},
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Gender vs Course Category Heatmap")
    heat_gender = pd.crosstab(fdf["Gender"], fdf["CourseCategory"])
    fig = px.imshow(
        heat_gender, text_auto=True, aspect="auto", color_continuous_scale="Purples",
        labels=dict(x="Course Category", y="Gender", color="Enrollments"),
        title="Enrollment Intensity: Gender vs Course Category",
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Tab 4: Category popularity  ----
with tab4:
    st.subheader("Course Category & Level Popularity")

    c1, c2 = st.columns(2)
    with c1:
        cat_pop = fdf["CourseCategory"].value_counts().reset_index()
        cat_pop.columns = ["CourseCategory", "Enrollments"]
        fig = px.bar(
            cat_pop.sort_values("Enrollments"), x="Enrollments", y="CourseCategory",
            orientation="h", title="Category Popularity Index (Total Enrollments)",
            color="Enrollments", color_continuous_scale="Tealgrn",
        )
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        level_pop = fdf["CourseLevel"].value_counts().reindex(["Beginner", "Intermediate", "Advanced"]).fillna(0)
        fig = px.pie(
            names=level_pop.index, values=level_pop.values,
            title="Level Preference Distribution", hole=0.4,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Most & Least Popular Categories")
    c3, c4 = st.columns(2)
    c3.success(f"**Most Popular:** {cat_pop.iloc[0]['CourseCategory']} ({int(cat_pop.iloc[0]['Enrollments'])} enrollments)")
    c4.error(f"**Least Popular:** {cat_pop.iloc[-1]['CourseCategory']} ({int(cat_pop.iloc[-1]['Enrollments'])} enrollments)")

    st.markdown("##### Course Type (Paid/Free) Split by Category")
    type_cat = fdf.groupby(["CourseCategory", "CourseType"], observed=True).size().reset_index(name="Enrollments")
    fig = px.bar(
        type_cat, x="CourseCategory", y="Enrollments", color="CourseType",
        barmode="stack", title="Paid vs Free Enrollments by Category",
    )
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

# --- Tab 5: Segment deep-dive / behavioral insights --------------------------
with tab5:
    st.subheader("Behavioral Insights & Segment Deep-Dive")

    c1, c2, c3 = st.columns(3)
    courses_per_user = fdf.groupby("UserID").size()
    c1.metric("Avg Courses / Learner", f"{courses_per_user.mean():.2f}")
    c2.metric("Median Courses / Learner", f"{courses_per_user.median():.0f}")
    top10_share = courses_per_user.sort_values(ascending=False).head(int(0.1 * len(courses_per_user)) or 1).sum() / total_enrollments * 100
    c3.metric("Enrollment Share: Top 10% Learners", f"{top10_share:.1f}%")

    st.markdown("##### Distribution of Courses Taken per Learner")
    fig = px.histogram(courses_per_user, nbins=20, labels={"value": "Courses Taken"}, title="Enrollment Concentration Across Learners")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Beginner vs Advanced Learner Behavior")
    level_age = fdf.groupby(["CourseLevel", "AgeGroup"], observed=True).size().reset_index(name="Enrollments")
    fig = px.bar(
        level_age, x="CourseLevel", y="Enrollments", color="AgeGroup",
        barmode="group", title="Course Level Uptake by Age Group",
        category_orders={"CourseLevel": ["Beginner", "Intermediate", "Advanced"], "AgeGroup": AGE_LABELS},
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Monthly Enrollment Trend")
    monthly = fdf.set_index("TransactionDate").resample("ME").size().reset_index(name="Enrollments")
    fig = px.line(monthly, x="TransactionDate", y="Enrollments", markers=True, title="Enrollments Over Time")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander(" View Filtered Raw Data"):
        st.dataframe(
            fdf[["TransactionID", "UserID", "UserName", "Age", "Gender", "AgeGroup",
                 "CourseID", "CourseName", "CourseCategory", "CourseType", "CourseLevel",
                 "TransactionDate"]].sort_values("TransactionDate", ascending=False),
            use_container_width=True,
        )

st.markdown("---")
