from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QSizePolicy, QPushButton, QFileDialog,QShortcut,QColorDialog
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont,QIcon,QKeySequence
from PyQt5.uic import loadUiType
from reportlab.pdfgen import canvas
import os
import sys
import statistics
from fpdf import FPDF
from PIL import Image
import math
from statistics import mean, stdev
from PIL import Image
import pyqtgraph as pg
import numpy as np
import time
from PyQt5.QtWidgets import QMenu, QAction
from pyqtgraph.Qt import QtCore
from PyQt5.QtWidgets import QComboBox
import pyqtgraph as pg

# Set the PyQtGraph theme to light mode
pg.setConfigOption('background', 'w')  
pg.setConfigOption('foreground', 'k')  
pg.setConfigOption('antialias', True)  


# Define the list to store the names of signals
loaded_signal_filenames = []
loaded_signal_filenames_2 = []

# Load the UI file and get the main form class
UI_FILE = "Signal_Viewer.ui"
Ui_MainWindow, QMainWindowBase = loadUiType(os.path.join(os.path.dirname(__file__), UI_FILE))

class MainApp(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainApp, self).__init__(parent)
        QMainWindow.__init__(self)
        self.setupUi(self)


        #PlotWidget for displaying signal
        self.plotWidget = pg.PlotWidget()
        self.verticalLayout_6.addWidget(self.plotWidget)  

        #PlotWidget for the second signal
        self.plotWidget2 = pg.PlotWidget()
        self.verticalLayout_3.addWidget(self.plotWidget2) 

        #Handle each button to it's function in plot2
        self.pushButton_11.clicked.connect(self.select_signal_2)
        self.pushButton_17.clicked.connect(self.zoom_in_2)
        self.pushButton_18.clicked.connect(self.zoom_out_2)
        self.pushButton_19.clicked.connect(self.reset_view_2)
        self.pushButton_20.clicked.connect(self.clear_2)
        self.pushButton_13.clicked.connect(self.play_pause_2)
        self.pushButton_9.clicked.connect(self.move_down)
        self.pushButton_14.clicked.connect(self.hide_2)
        self.pushButton_15.clicked.connect(self.pdf_generate_2)

        #Handle each button to it's function in plot1
        self.pushButton_2.clicked.connect(self.select_signal)
        self.pushButton_3.clicked.connect(self.play_pause)
        self.pushButton_7.clicked.connect(self.clear)
        self.pushButton_4.clicked.connect(self.zoom_in)
        self.pushButton_5.clicked.connect(self.zoom_out)
        self.pushButton_6.clicked.connect(self.reset_view)
        self.pushButton_16.clicked.connect(self.show_hide_frame)
        self.pushButton_21.clicked.connect(self.move_up)
        self.pushButton_8.clicked.connect(self.hide)
        self.pushButton_10.clicked.connect(self.pdf_generate)
  
        # Variable to track whether signal is currently displayed or playing for plotWidgets
        self.signal_displayed_2 = False
        self.signal_playing_2 = False  

        self.signal_displayed = False
        self.signal_playing = False  

        # List to store loaded and ploted signals for plotWidgets
        self.loaded_signals_2 = []
        self.plot_items_2 = []

        self.loaded_signals = []
        self.plot_items = []

        # Zoom factor for plotWidgets 
        self.zoom_factor_2 = 1.0
        self.zoom_factor = 1.0

        # Create a QTimer to update the signal for plotWidgets
        self.signal_timer_2 = QTimer(self)
        self.signal_timer_2.timeout.connect(self.update_signal_2)
        self.signal_timer_2.start(100) 
        
        self.signal_timer = QTimer(self)
        self.signal_timer.timeout.connect(self.update_signal)
        self.signal_timer.start(100)  

        # Create a layout for widget
        self.layout_widget = QVBoxLayout()
        widget = QWidget()
        widget.setLayout(self.layout_widget)
        self.setCentralWidget(widget)

        # Create a layout for widget_2
        widget_2 = QWidget()
        self.setCentralWidget(widget_2)

        # Create a widget to hold the verticalLayout_2
        widget = QWidget()
        widget.setLayout(self.verticalLayout_2)

        # Set widget as the central widget to fill the entire window
        self.setCentralWidget(widget)

        # Create a QTimer to update the CSV data plot for plotWidget2
        self.csv_data_timer_2 = QTimer(self)
        self.csv_data_timer_2.timeout.connect(self.update_signal_2)
        
        self.pdf = canvas.Canvas('output.pdf')

        # Handle speed slider
        self.horizontalSlider.valueChanged.connect(self.update_csv_timer_interval_2)
        self.horizontalSlider_2.valueChanged.connect(self.update_csv_timer_interval)

        #Handle change color
        self.color_up.clicked.connect(self.open_color_palette)
        self.color_down.clicked.connect(self.open_color_palette_2)


        
        # Set app icon
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "logo.png")
        app_icon = QIcon(icon_path)
        self.setWindowIcon(app_icon)

        # Set app name
        self.setWindowTitle("Multi-Channel Signal Viewer")

        self.setStyleSheet('''
            QMainWindow {
                background-color: #00000;
            }
            QLabel {
                font-size: 14px;
                color: black; /* Text color for labels set to black */
            }
            QPushButton {
                background-color: white; /* Button background color set to white */
                color: black; /* Button text color set to black */
                border: 1px solid #CCCCFF; /* Border color */
                border-radius: 5px;
                padding: 5px 10px;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2); /* Adds a slight shadow */
            }
            QPushButton:hover {
                background-color: #CCCCFF; /* Hover background color - light cyan */
                color: black; /* Change text color on hover to black */
            }
        ''')


        # Apply margins to the verticalLayout_2
        self.verticalLayout_2.setContentsMargins(20, 20, 20, 20)  # Adjust the margins as needed

        # Initialize CSV data
        self.signal = None
        self.signal_phase = 0.0
        self.rows_to_display = 2000  
        self.current_row = 0  
        self.transition_duration = 1000  # Duration of transition between rows in milliseconds
        self.transition_timer = QTimer(self)
        self.transition_timer.timeout.connect(self.increment_current_row)

    #Handle select signal for the two plots
    def select_signal(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        options |= QFileDialog.ExistingFiles

        file_dialog = QFileDialog(self)
        file_dialog.setOptions(options)
        file_dialog.setWindowTitle("Open CSV File")
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilters(["CSV Files (*.csv)", "All Files (*)"])

        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            for file_path in selected_files:
                self.load_signal(file_path)

    def select_signal_2(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        options |= QFileDialog.ExistingFiles

        file_dialog = QFileDialog(self)
        file_dialog.setOptions(options)
        file_dialog.setWindowTitle("Open CSV File for plotWidget2")
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilters(["CSV Files (*.csv)", "All Files (*)"])

        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            for file_path in selected_files:
                self.load_signal_2(file_path)

    #Handle loading and setting signals in the two graphs
    def load_signal(self, file_path):
        # Load and set the CSV data
        try:
            data = np.genfromtxt(file_path, delimiter=',')  
            self.loaded_signals.append(data)
            self.signal_displayed = True
            self.current_row = 0  
            loaded_signal_filenames_2.append(os.path.basename(file_path))
            self.combo_box_bottom()
        except Exception as e:
            print(f"Error loading CSV data: {str(e)}")
            self.loaded_signals.append(None)
            self.signal_displayed = False

    def load_signal_2(self, file_path):
        try:
            data = np.genfromtxt(file_path, delimiter=',')  
            self.loaded_signals_2.append(data)
            self.signal_displayed_2 = True
            self.current_row = 0  
            loaded_signal_filenames.append(os.path.basename(file_path))
            self.combo_box()
        except Exception as e:
            print(f"Error loading CSV data for plotWidget2: {str(e)}")
            self.loaded_signals_2.append(None)
            self.signal_displayed_2 = False

    #Handle plot1 buttons
    def play_pause(self):
        if not self.signal_displayed:
            return
        
        if self.signal_playing:
            self.signal_timer.stop()
            self.pushButton_3.setText("Play")
        else:
            self.signal_timer.start(100)  
            self.pushButton_3.setText("Pause")

        self.signal_playing = not self.signal_playing

    def clear(self):
        self.loaded_signals = []  
        self.signal_displayed = False
        self.plotWidget.clear()  
        self.pushButton_3.setText("Play")
        self.signal_playing = False
        self.cB_loadcsvbottom.clear()

    def zoom_in(self):
        if self.zoom_factor > 0.2:
            self.zoom_factor -= 0.2

    def zoom_out(self):
        if self.zoom_factor < 4.0:
            self.zoom_factor += 0.2

    def reset_view(self):
        self.zoom_factor = 1.0

    def combo_box(self):
        self.cB_loadcsvtop.clear()  
        self.cB_loadcsvtop.addItems(loaded_signal_filenames)   

    def hide(self):
        selected_index = self.cB_loadcsvbottom.currentIndex()

        if selected_index >= 0 and selected_index < len(self.loaded_signals):
            data_to_hide = self.loaded_signals.pop(selected_index)
            filename = loaded_signal_filenames_2.pop(selected_index)

            self.combo_box()
            self.combo_box_bottom()
            self.loaded_signals.pop(data_to_hide)
            self.update_signal()
            self.combo_box_bottom()

    #Handle plot2 buttons   
    def play_pause_2(self):
        if not self.signal_displayed_2:
            return

        if self.signal_playing_2:
            self.signal_timer_2.stop()
            self.pushButton_13.setText("Play")
        else:
            self.signal_timer_2.start(100)  
            self.pushButton_13.setText("Pause")
        
        self.signal_playing_2 = not self.signal_playing_2

    def clear_2(self):
        self.loaded_signals_2 = []  
        self.signal_displayed_2 = False
        self.plotWidget2.clear()  
        self.pushButton_13.setText("Play")
        self.signal_playing_2 = False
        self.cB_loadcsvtop.clear()

    def zoom_in_2(self):
        if self.zoom_factor_2 > 0.2:
            self.zoom_factor_2 -= 0.2
            
    def zoom_out_2(self):
        if self.zoom_factor_2 < 4.0:
            self.zoom_factor_2 += 0.2

    def reset_view_2(self):
        self.zoom_factor_2 = 1.0

    def combo_box_bottom(self):
        self.cB_loadcsvbottom.clear()  
        self.cB_loadcsvbottom.addItems(loaded_signal_filenames_2)    
    
    def hide_2(self):
        selected_index = self.cB_loadcsvtop.currentIndex()

        if selected_index >= 0 and selected_index < len(self.loaded_signals_2):
            data_to_hide = self.loaded_signals_2.pop(selected_index)
            filename = loaded_signal_filenames.pop(selected_index)

            # Update the combo box for plotWidget2
            self.combo_box()
            self.combo_box_bottom()

            # Move the data to plotWidget2
            self.loaded_signals_2.pop(data_to_hide)

            # Update the plot for both plotWidgets
            self.update_signal()

            # Clear the combo box for plotWidget (cB_loadcsvtop) and add items
            self.combo_box()


    #Handle link button 
    def show_hide_frame(self):
        if self.frame.isHidden():
            self.frame.show()
            self.horizontalSlider.show()
            self.label_3.show()
            self.pushButton_16.setText("Link")  
            self.pushButton_13.clicked.disconnect(self.play_pause)
            self.pushButton_11.clicked.disconnect(self.select_signal)
            self.pushButton_17.clicked.disconnect(self.zoom_in)
            self.pushButton_18.clicked.disconnect(self.zoom_out)
            self.pushButton_19.clicked.disconnect(self.reset_view)
            self.pushButton_20.clicked.disconnect(self.clear)
            self.pushButton_21.clicked.disconnect(self.update_signal)
        else:
            self.frame.hide()
            self.horizontalSlider.hide()
            self.label_3.hide()
            self.pushButton_16.setText("Unlink")  
            self.pushButton_13.clicked.connect(self.play_pause)
            self.pushButton_11.clicked.connect(self.select_signal)
            self.pushButton_17.clicked.connect(self.zoom_in)
            self.pushButton_18.clicked.connect(self.zoom_out)
            self.pushButton_19.clicked.connect(self.reset_view)
            self.pushButton_20.clicked.connect(self.clear)

    #Handle signal playing and replay
    def update_signal(self):
        if self.signal_displayed and self.signal_playing:
            self.plotWidget.clear()
            for data_index, data in enumerate(self.loaded_signals):
                if data is not None:
                    start_row = self.current_row
                    end_row = self.current_row + int(self.rows_to_display * self.zoom_factor)

                    if end_row > len(data):
                        end_row = len(data)

                    if start_row < len(data):
                        color = 'b' if data_index == 0 else 'r'
                        x_values = np.arange(start_row, end_row)
                        shifted_data = data[start_row:end_row]
                        self.plotWidget.plot(x_values, shifted_data, pen=color)
            self.current_row += 1
            if self.current_row + int(self.rows_to_display * self.zoom_factor) > len(self.loaded_signals[0]):
                self.current_row = 0  
        self.update_data_signal.emit()

    def update_signal_2(self):
        if self.signal_displayed_2 and self.signal_playing_2:
            self.plotWidget2.clear()
            for data_index, data in enumerate(self.loaded_signals_2):
                if data is not None:
                    start_row = self.current_row
                    end_row = self.current_row + int(self.rows_to_display * self.zoom_factor_2)

                    if end_row > len(data):
                        end_row = len(data)

                    if start_row < len(data):
                        color = 'b' if data_index == 0 else 'r'
                        x_values = np.arange(start_row, end_row)
                        shifted_data = data[start_row:end_row]
                        self.plotWidget2.plot(x_values, shifted_data, pen=color)

            self.current_row += 1
            if self.current_row + int(self.rows_to_display * self.zoom_factor_2) > len(self.loaded_signals_2[0]):
                self.current_row = 0  
        self.update_data_signal.emit()

    def increment_current_row(self):
        # Increment the current row and reset the transition timer
        self.current_row += 1
        if self.current_row + int(self.rows_to_display * self.zoom_factor) > len(self.loaded_signals[0]):
            self.current_row = 0  # Wrap around to the beginning
        self.transition_timer.start(self.transition_duration)

    def update_csv_timer_interval_2(self, value):
        # Update the update interval of the CSV data timer for plotWidget2
        self.signal_timer_2_interval = value
        if self.signal_playing_2:
            self.signal_timer_2.start(self.signal_timer_2_interval)

    def update_csv_timer_interval(self, value):
        # Update the update interval of the CSV data timer for plotWidget
        self.signal_timer_interval = value
        if self.signal_playing:
            self.signal_timer.start(self.signal_timer_interval)
    
    #Handle moving signals from graph to another
    def move_up(self):
        selected_index = self.cB_loadcsvbottom.currentIndex()

        if selected_index >= 0 and selected_index < len(self.loaded_signals):
            data_to_move = self.loaded_signals.pop(selected_index)
            filename = loaded_signal_filenames_2.pop(selected_index)

            self.combo_box()
            self.combo_box_bottom()
            self.loaded_signals_2.append(data_to_move)
            loaded_signal_filenames.append(filename)
            self.combo_box()
            self.update_signal()

    def move_down(self):
        selected_index = self.cB_loadcsvtop.currentIndex()
        
        if selected_index >= 0 and selected_index < len(self.loaded_signals_2):
            data_to_move = self.loaded_signals_2.pop(selected_index)
            filename = loaded_signal_filenames.pop(selected_index)
            
            self.combo_box()
            self.combo_box_bottom()
            self.loaded_signals.append(data_to_move)
            loaded_signal_filenames_2.append(filename)
            self.combo_box_bottom()
            self.update_signal_2()

    #Handle change color 
    def open_color_palette(self):
        color = QColorDialog.getColor()
        if color.isValid():    
            selected_index = self.cB_loadcsvtop.currentIndex()
            if selected_index >= 0 and selected_index < len(loaded_signal_filenames_2):
                self.plotWidget2.plotItem.items[selected_index].setPen(color)

    def open_color_palette_2(self):
        color = QColorDialog.getColor()
        if color.isValid():
            selected_index = self.cB_loadcsbottom.currentIndex()
            if selected_index >= 0 and selected_index < len(loaded_signal_filenames):
                self.plotWidget.plotItem.items[selected_index].setPen(color)  

    #Generate pdf for graph1 "above"
    def pdf_generate(self):

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Times", size=10)

        page_width = pdf.w - 4 * pdf.l_margin
        col_width = page_width / 8  
        line_height = pdf.font_size * 2.5

        first_page_image_path = r"heartbeat-163709_1920.jpg"
        img = Image.open(first_page_image_path)
        img_width, img_height = img.size
        img_width, img_height = img_width * 0.25, img_height * 0.43  # Adjust image size if needed
        pdf.image(first_page_image_path, x=10, y=30, w=img_width, h=img_height)

        pdf.add_page()

        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Image files (*.png *.jpg *.jpeg *.gif *.bmp);;All files (*)")
        file_paths, _ = file_dialog.getOpenFileNames()
        max_image_width = img_width
        y_position = 5
        x_position = 5
        image_count = 0  
        max_images_per_column = 2

        for file_path1 in file_paths:
            img = Image.open(file_path1)
            img_width, img_height = img.size
            new_width = max_image_width
            new_height = (img_height / img_width) * new_width

            img_width, img_height = img_width * 0.1, img_height * 0.1  
            pdf.image(file_path1, x=x_position, y=y_position, w=img_width, h=img_height)
            title = "Graph two"  
            pdf.set_xy(x_position, y_position + img_height + 5)  
            pdf.cell(img_width, 10, title, 0, 1, "C")
            x_position += img_width 
            if x_position > max_image_width:
                x_position = 5
                y_position += img_height 
            image_count += 1
            if image_count == max_images_per_column:
                x_position = 5
                y_position += new_height + 5
                image_count = 0
            headers = ["Statistics", "Value"]
            table_x = 10
            table_y = 60
            col_width = 70
            row_height = 12
            data_1 = []

            try:
                for data in self.loaded_signals_2:
                    if data is not None:
                      data_1.append(data)

            except Exception as e:
               print(f"Error loading CSV data for PDF generation: {str(e)}")
               continue
            mean_value = np.mean(data_1)
            std_deviation = np.std(data_1)
            median_value = np.median(data_1)

            data = [
                ("Mean", mean_value),
                ("Std Dev", std_deviation),
                ("Median", median_value)
            ]
            pdf.set_fill_color(0, 123, 255)
            pdf.set_text_color(255, 255, 255)
            pdf.set_xy(table_x, table_y)
            pdf.cell(col_width, row_height, headers[0], 1, 0, "C", 1)
            pdf.cell(col_width, row_height, headers[1], 1, 1, "C", 1)

            pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(0, 0, 0)
            fill = 0  
            for row in data:
                pdf.set_xy(table_x, table_y + row_height)
                for item in row:
                    pdf.cell(col_width, row_height, str(item), 1, 0, "C", fill)
                fill = 1 - fill
                table_y += row_height
            pdf.output('report.pdf')      

#Handle Generate report for graph2 
    def pdf_generate_2(self):

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Times", size=10)
        page_width = pdf.w - 4 * pdf.l_margin
        col_width = page_width / 8  
        line_height = pdf.font_size * 2.5
        first_page_image_path = r"heartbeat-163709_1920.jpg"
        img = Image.open(first_page_image_path)
        img_width, img_height = img.size
        img_width, img_height = img_width * 0.25, img_height * 0.43  
        pdf.image(first_page_image_path, x=10, y=30, w=img_width, h=img_height)
        pdf.add_page()
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Image files (*.png *.jpg *.jpeg *.gif *.bmp);;All files (*)")
        file_paths, _ = file_dialog.getOpenFileNames()
        max_image_width = img_width
        y_position = 5
        x_position = 5
        image_count = 0  
        max_images_per_column = 2

        for file_path1 in file_paths:
            img = Image.open(file_path1)
            img_width, img_height = img.size
            new_width = max_image_width
            new_height = (img_height / img_width) * new_width

            img_width, img_height = img_width * 0.1, img_height * 0.1  
            pdf.image(file_path1, x=x_position, y=y_position, w=img_width, h=img_height)
            title = "Graph one"  
            pdf.set_xy(x_position, y_position + img_height + 5)  
            pdf.cell(img_width, 10, title, 0, 1, "C")

            x_position += img_width  
            if x_position > max_image_width:
                x_position = 5
                y_position += img_height  
            image_count += 1
            if image_count == max_images_per_column:
                x_position = 5
                y_position += new_height + 5
                image_count = 0
            headers = ["Statistics", "Value"]
            table_x = 10
            table_y = 60
            col_width = 70
            row_height = 12
            data_1 = []
            try:
                for data in self.loaded_signals:
                    if data is not None:
                      data_1.append(data)
            except Exception as e:
               print(f"Error loading CSV data for PDF generation: {str(e)}")
               continue
            mean_value = np.mean(data_1)
            std_deviation = np.std(data_1)
            median_value = np.median(data_1)

            data = [
                ("Mean", mean_value),
                ("Std Dev", std_deviation),
                ("Median", median_value)
            ]

            pdf.set_fill_color(0, 123, 255)
            pdf.set_text_color(255, 255, 255)
            pdf.set_xy(table_x, table_y)
            pdf.cell(col_width, row_height, headers[0], 1, 0, "C", 1)
            pdf.cell(col_width, row_height, headers[1], 1, 1, "C", 1)

            pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(0, 0, 0)
            fill = 0  
            for row in data:
                pdf.set_xy(table_x, table_y + row_height)
                for item in row:
                    pdf.cell(col_width, row_height, str(item), 1, 0, "C", fill)
                fill = 1 - fill
                table_y += row_height
            pdf.output('report.pdf')      
#Handle shortcuts
#plot widget 2
def shortcut_play_pause_2():
    window.play_pause_2()
    
def shortcut_clear_2():
    window.clear_2()

def shortcut_reset_view_2():
    window.reset_view_2()

def shortcut_zoom_out_2():
    window.zoom_out_2()

def shortcut_zoom_in_2():
    window.zoom_in_2()

def shortcut_select_signal_2():
    window.select_signal_2()

def shortcut_link_plots():
    window.show_hide_frame()
    
def shortcut_move_down():
    window.move_down()

#for plot widget 1 
def shortcut_play_pause():
    window.play_pause()
    
def shortcut_clear():
    window.clear()

def shortcut_reset_view():
    window.reset_view()

def shortcut_zoom_out():
    window.zoom_out()

def shortcut_zoom_in():
    window.zoom_in()

def shortcut_select_signal():
    window.select_signal()

def shortcut_move_up():
    window.move_up()    
        
    # ...

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainApp()
    window.showMaximized()


    #shortcuts keybinds  
    # For Plot_Widget_2
    shortcut_play_2 = QShortcut(QKeySequence("ctrl+R"),window)
    shortcut_play_2.activated.connect(shortcut_play_pause_2)
    
    shortcut_clear2 = QShortcut(QKeySequence("ctrl+End"),window)
    shortcut_clear2.activated.connect(shortcut_clear_2)
        
    shortcut_update_2 = QShortcut(QKeySequence("ctrl+U"),window)
    shortcut_update_2.activated.connect(shortcut_reset_view_2)

    shortcut_minus_2 = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Minus),window)
    shortcut_minus_2.activated.connect(shortcut_zoom_out_2)
   
    shortcut_plus_2 = QShortcut(QKeySequence("Ctrl+="),window)
    shortcut_plus_2.activated.connect(shortcut_zoom_in_2)
    
    shortcut_select_signal_plot_2 = QShortcut(QKeySequence("Ctrl+O"),window)
    shortcut_select_signal_plot_2.activated.connect(shortcut_select_signal_2)

    shortcut_link_plots_together = QShortcut(QKeySequence("ctrl+L"),window)
    shortcut_link_plots_together.activated.connect(shortcut_link_plots)

    shortcut_move_graph_down = QShortcut(QKeySequence("Tab"),window)
    shortcut_move_graph_down.activated.connect(shortcut_move_down)

    #for Plot_widget_1    
    shortcut_play_1 = QShortcut(QKeySequence("ctrl+P"),window)
    shortcut_play_1.activated.connect(shortcut_play_pause)
    
    shortcut_clear_1 = QShortcut(QKeySequence("ctrl+Delete"),window)
    shortcut_clear_1.activated.connect(shortcut_clear)
        
    shortcut_update_1 = QShortcut(QKeySequence("ctrl+H"),window)
    shortcut_update_1.activated.connect(shortcut_reset_view)

    shortcut_minus_1 = QShortcut(QKeySequence(Qt.AltModifier + Qt.Key_Up), window)
    shortcut_minus_1.activated.connect(shortcut_zoom_out)
   
    shortcut_plus_1 = QShortcut(QKeySequence(Qt.AltModifier + Qt.Key_Down),window)
    shortcut_plus_1.activated.connect(shortcut_zoom_in)
    
    shortcut_select_signal_plot_1 = QShortcut(QKeySequence("Ctrl+N"),window)
    shortcut_select_signal_plot_1.activated.connect(shortcut_select_signal)

    shortcut_move_graph_up = QShortcut(QKeySequence("Shift+Tab"),window)
    shortcut_move_graph_up.activated.connect(shortcut_move_up)

    sys.exit(app.exec_())


