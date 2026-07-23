# EduPro Learner Analytics Dashboard

A Streamlit app that joins **Users**, **Courses**, and **Transactions** data
(via `UserID` and `CourseID`) to answer EduPro's key learner-analytics questions.

## Files
- `app.py` - the Streamlit application
- `EduPro_Online_Platform.xlsx` - source dataset (Users, Teachers, Courses, Transactions sheets)
- `requirements.txt` - Python dependencies



**Sidebar filters:** Age Group, Gender, Course Category, Course Level, Course Type (Paid/Free), Transaction Date Range.

**Top KPI strip:** Total Enrollments, Active Learners, Avg Courses/Learner, Top Course Category, Gender Split.

**Tabs:**
1. **Demographic Overview** - age-group bar chart, gender pie chart, age histogram by gender, participation by age × gender.
2. **Age-wise Enrollment** - course level & type uptake by age group, age-group × category heatmap.
3. **Gender Preferences** - category & level preference by gender, gender × category heatmap.
4. **Category Popularity** - category popularity index, level preference pie, most/least popular category callouts, paid/free split by category.
5. **Segment Deep-Dive** - courses-per-learner distribution, enrollment concentration among top learners, beginner-vs-advanced behavior by age, monthly enrollment trend, and a filterable raw data table.

All charts respond live to the sidebar filters, so you can drill into any specific
age group, gender, category, or level combination.
