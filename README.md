# hoysportsdata.com

A professional web application for analyzing football team self-scout data. Convert your Excel self-scout files into interactive, professional analytics with beautiful visualizations.

## Features

- **Easy File Upload**: Drag and drop Excel files (.xlsx, .xls)
- **Multi-Sheet Analysis**: Select and analyze multiple sheets from your Excel file
- **Advanced Statistics**: 
  - Run vs Pass distribution analysis
  - Stat comparisons across different play types
  - Calculated metrics (Avg Yards, Scramble %, etc.)
  - Efficiency, Negative Play %, Explosive Play %, and more
- **Interactive Visualizations**: Professional charts powered by Altair/Vega-Lite
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Supported Statistics

### Calculated Metrics
- **Avg Yards (Calculated)**: Total yards per sheet ÷ total calls per sheet
- **Scramble %**: Total scrambles per sheet ÷ total calls per sheet × 100

### Percentage Metrics
- **Efficiency %**: Situational efficiency calculations
- **Negative %**: Negative plays percentage
- **Explosive %**: Explosive plays percentage  
- **Completion %**: Pass completion percentage
- **Pressure %**: Pressure percentage

### Raw Statistics
- Total yards, completions, calls, scrambles, and more

## Installation

1. **Clone or download** this repository
2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   python app.py
   ```
4. **Open your browser** to `http://localhost:5000`

## Usage

1. **Upload Your Excel File**: Drag and drop or click to select your self-scout Excel file
2. **Select Sheets**: Choose which sheets from your Excel file to include in the analysis
3. **Analyze Data**: Click "Analyze Data" to process your file
4. **View Results**: 
   - See summary statistics
   - View run vs pass distribution
   - Compare specific statistics across sheets
   - Explore interactive charts

## File Requirements

- **Format**: Excel files (.xlsx or .xls)
- **Size**: Maximum 16MB
- **Structure**: Should contain columns like:
  - `calls` - Number of plays
  - `total yards` or `gain` - Yards gained
  - `scrambles` - Scramble plays (if applicable)
  - Other statistical columns as needed

## Deployment

### Local Development
```bash
python app.py
```

### Production Deployment
The app is ready for deployment on platforms like:
- **Heroku**: Use the included `requirements.txt`
- **AWS**: Deploy with Elastic Beanstalk or EC2
- **DigitalOcean**: Use App Platform
- **Vercel**: Deploy with serverless functions

For production, set `debug=False` in `app.py`.

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Data Processing**: Pandas
- **Visualizations**: Altair/Vega-Lite
- **File Handling**: OpenPyXL, xlrd

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## Contributing

This is a specialized tool for football analytics. For feature requests or bug reports, please contact the development team.

## License

© 2025 hoysportsdata.com - Professional Football Analytics

---

**Professional football team self-scout analysis made simple and beautiful.**
