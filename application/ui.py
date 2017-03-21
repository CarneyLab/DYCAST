#! /usr/bin/env python

# The Graphical User Interface for manual operation of the DYCAST system

from Tkinter import *
import tkFileDialog, tkMessageBox
import os
import dycast
import datetime
import optparse
import fileinput
import ttk

usage = "usage: %prog [options]"
p = optparse.OptionParser(usage)
p.add_option('--config', '-c', 
            default="./dycast.config", 
            help="load config file FILE", 
            metavar="FILE")

options, arguments = p.parse_args()

config_file = options.config

class DYCAST_control(ttk.Frame):
    def connect_to_DYCAST(self):
        dycast.read_config(config_file)
        dycast.init_db()
        dycast.init_logging()
        

    def load_birds(self):
        self.status_label["text"] = "Status: loading birds..."
        self.status_label.update_idletasks()
        self.load_birds_button["state"] = DISABLED
        self.files = self.load_birds_entry.get()
        self.files = self.files.split(" ")
        try:
            for file in self.files:
                dir, base = os.path.split(file)
                self.status_label["text"] = "Status: loading birds... %s" % base
                self.status_label.update_idletasks()
                dycast.load_bird_file(file)
        except:
            if (self.files):
                tkMessageBox.showwarning(
                    "Open file",
                    "Cannot open file(s): %s" % self.files
                )
            else:
                tkMessageBox.showwarning(
                    "Open file",
                    "No files selected"
                )
            
        self.load_birds_button["state"] = NORMAL
        self.status_label["text"] = "Status: ready"
        self.status_label.update_idletasks()

    def set_bird_file(self):
        #file = tkFileDialog.askopenfile(parent=self, mode='rb', title="select dead bird files")
        self.files = tkFileDialog.askopenfilenames(parent=self, title="select dead bird files")
        self.load_birds_entry.delete(0, END)
        self.load_birds_entry.insert(0, self.files)

    def set_export_dir(self):
        self.export_dir = tkFileDialog.askdirectory(parent=self, title="choose export directory")
        self.export_dir_entry.delete(0, END)
        self.export_dir_entry.insert(0, self.export_dir)

    def set_kappa_export_dir(self):
        self.kappa_export_dir = tkFileDialog.askdirectory(parent=self, title="choose export directory")
        self.kappa_export_dir_entry.delete(0, END)
        self.kappa_export_dir_entry.insert(0, self.kappa_export_dir)

    def get_date_range(self, datestring1, datestring2):
        (y,m,d) = datestring1.split('-')
        startdate = datetime.date(int(y), int(m), int(d))
        (y,m,d) = datestring2.split('-')
        enddate = datetime.date(int(y), int(m), int(d))

        datediff = startdate - enddate
        if (enddate > startdate):
            firstdate = startdate
            lastdate = enddate
        else:
            lastdate = startdate
            firstdate = enddate
        curdate = startdate
        return (curdate, lastdate)

    def get_date_iterator(self, datestring1, datestring2):
        (y,m,d) = datestring1.split('-')
        startdate = datetime.date(int(y), int(m), int(d))
        (y,m,d) = datestring2.split('-')
        enddate = datetime.date(int(y), int(m), int(d))
        return range(startdate, enddate)
        
    def run_daily_risk(self):
        self.status_label["text"] = "Status: generating risk..."
        self.status_label.update_idletasks()
        self.daily_risk_button["state"] = DISABLED

        (curdate, enddate) = self.get_date_range(
            self.daily_risk_entry1.get(),
            self.daily_risk_entry2.get()
        )
        oneday = datetime.timedelta(days=1)
        
        # TODO: really, I should query the databsae to see which possible parameter
        # sets exist, and offer these to the user instead of letting them specify
        # their own.
        
        cs = self.daily_risk_cs_entry.get()
        ct = self.daily_risk_ct_entry.get()
        sd = self.daily_risk_sd_entry.get()
        td = self.daily_risk_td_entry.get()
        
        param_id = dycast.get_param_record_id(cs, ct, sd, td)
        if not param_id:
            tkMessageBox.showerror(
                "Daily risk",
                "Cannot run daily risk: monte carlo simulations have not been generated for this set of parameters. Choose different parameters, or generate them from the Initialization window."
            )
        else:
            while (curdate <= enddate):
                self.status_label["text"] = "Status: generating risk... %s" % curdate
                self.status_label.update_idletasks()
                try:
                    dycast.daily_risk(curdate, cs, ct, sd, td)
                    #dycast.daily_risk(curdate, cs, ct, sd, td, 5580000, 5710000) # for testing
                except:
                    tkMessageBox.showwarning(
                        "Daily risk",
                        "Could not run daily risk for %s" % curdate
                    )
                    break
                curdate = curdate + oneday

        self.daily_risk_button["state"] = NORMAL
        self.status_label["text"] = "Status: ready"
        self.status_label.update_idletasks()

    def run_export_risk(self):
        self.status_label["text"] = "Status: exporting risk..."        
        self.status_label.update_idletasks()
        self.export_risk_button["state"] = DISABLED

        (curdate, enddate) = self.get_date_range(
            self.export_risk_entry1.get(),
            self.export_risk_entry2.get()
        )

        oneday = datetime.timedelta(days=1)

        while (curdate <= enddate):
            self.status_label["text"] = "Status: exporting risk... %s" % curdate
            self.status_label.update_idletasks()
            self.export_dir = self.export_dir_entry.get()
            try:
                dycast.export_risk(curdate, "dbf", self.export_dir)
            except Exception, inst:
                tkMessageBox.showwarning(
                    "Export risk",
                    "Could not export daily risk for %s: %s" % (curdate, inst)
                )
                break
            curdate = curdate + oneday
        # Working here. TODO: what was I doing?

        self.export_risk_button["state"] = NORMAL
        self.status_label["text"] = "Status: ready"
        self.status_label.update_idletasks()
 
    def run_kappa(self):
        self.status_label["text"] = "Status: performing kappa analysis..."
        self.status_label.update_idletasks()
        self.kappa_button["state"] = DISABLED
        
        (startdate, enddate) = self.get_date_range(
            self.kappa_startdate_entry.get(),
            self.kappa_enddate_entry.get()
        )
        window_start = int(self.kappa_window_start_entry.get())
        window_end = int(self.kappa_window_end_entry.get())
        window_step = int(self.kappa_window_step_entry.get())
        lag_start = int(self.kappa_lag_start_entry.get())
        lag_end = int(self.kappa_lag_end_entry.get())
        lag_step = int(self.kappa_lag_step_entry.get())
        
        useanalysisarea = False
        
        if window_start > window_end:
            tkMessageBox.showwarning(
                "Kappa",
                "value for window_start must be less than or equal to window_end"
            )
        elif lag_start > lag_end:
            tkMessageBox.showwarning(
                "Kappa",
                "value for lag_start must be less than or equal to lag_end"
            )
        elif window_step < 1:
            tkMessageBox.showwarning(
                "Kappa",
                "value for window_step must be greater than or equal to 1"
            )
        elif lag_step < 1:
            tkMessageBox.showwarning(
                "Kappa",
                "value for lag_step must be greater than or equal to 1"
            )
        else:             
            filehandle = dycast.init_kappa_output(self.kappa_export_dir_entry.get() + os.sep + self.kappa_export_file_entry.get())
            for window in range(window_start, window_end+window_step, window_step):
                for lag in range(lag_start, lag_end+lag_step, lag_step):
                    self.status_label["text"] = "Status: performing kappa analysis... window %s, lag %s" % (window, lag)
                    self.status_label.update_idletasks()
                    try:
                        if useanalysisarea:
                            print dycast.kappa(window, lag, startdate, enddate, dycast.get_analysis_area_id(), filehandle)
                        else:
                            print dycast.kappa(window, lag, startdate, enddate, None, filehandle)
                    except Exception, inst:
                        tkMessageBox.showwarning(
                            "Kappa",
                            "Could not calculate kappa for window %s, lag %s, startdate %s, enddate %s: %s" % (window, lag, startdate, enddate, inst)
                        )            
            dycast.close_kappa_output(filehandle)
            
        self.kappa_button["state"] = NORMAL
        self.status_label["text"] = "Status: ready"
        self.status_label.update_idletasks()
        
    def run_nmcm(self):
        self.status_label["text"] = "Status: running monte carlo simulations..."
        self.status_label.update_idletasks()
        self.kappa_button["state"] = DISABLED
        
        closespace = float(self.nmcm_close_space_entry.get())
        closetime = int(self.nmcm_close_time_entry.get())
        spatialdomain = float(self.nmcm_spatial_domain_entry.get())
        temporaldomain = int(self.nmcm_temporal_domain_entry.get())
        startnumber = int(self.nmcm_start_number_entry.get())
        endnumber = int(self.nmcm_end_number_entry.get())
        
        for birdnumber in range(startnumber, endnumber):
          self.status_label["text"] = "Status: running monte carlo simulations with %s birds..." % birdnumber 
          self.status_label.update_idletasks()
          dycast.create_dist_margs(closespace, closetime, spatialdomain, temporaldomain, birdnumber, birdnumber)

        self.status_label["text"] = "Status: calculating cumulative probabilities, almost finished..."
        self.status_label.update_idletasks()
        dycast.calculate_probabilities()
        
        self.kappa_button["state"] = NORMAL
        self.status_label["text"] = "Status: ready"
        self.status_label.update_idletasks()
        
    def set_nmcm_import_file(self):
        self.files = tkFileDialog.askopenfilenames(parent=self, title="select dead bird files")
        self.nmcm_load_file_entry.delete(0, END)
        self.nmcm_load_file_entry.insert(0, self.files)
        
    def load_nmcm(self):
        self.status_label["text"] = "Status: loading monte carlo results..."
        self.status_label.update_idletasks()
        self.nmcm_load_button["state"] = DISABLED
       
        closespace = float(self.nmcm_load_cs_entry.get())
        closetime = int(self.nmcm_load_ct_entry.get())
        spatialdomain = float(self.nmcm_load_sd_entry.get())
        temporaldomain = int(self.nmcm_load_td_entry.get())
        
        self.files = self.nmcm_load_file_entry.get()
        self.files = self.files.split(" ")
        try:
            for file in self.files:
                dir, base = os.path.split(file)
                self.status_label["text"] = "Status: loading monte carlo results... %s" % base
                self.status_label.update_idletasks()
                dycast.load_prepared_dist_margs(closespace, closetime, spatialdomain, temporaldomain, file)
        except Exception, inst:
            if (self.files):
                tkMessageBox.showwarning(
                    "Open file",
                    "Cannot open file(s): %s, message: %s" % (self.files, inst)
                )
            else:
                tkMessageBox.showwarning(
                    "Open file",
                    "No files selected"
                )

        self.nmcm_load_button["state"] = NORMAL
        self.status_label["text"] = "Status: ready"
        self.status_label.update_idletasks()
        
    def createWidgets(self):
        
        self.n = ttk.Notebook(self)
            
        self.n.grid(column=0, row=0)
        
        self.daily_frame = ttk.Frame(self.n)
        self.postseason_frame = ttk.Frame(self.n)
        self.init_frame = ttk.Frame(self.n)

        # Begin "daily tasks" page in the notebook
        
        self.label2 = ttk.Label(self.daily_frame)
        self.label2["text"] = "load dead birds from file(s):\n"
        self.label2.grid(column=0, row=0, columnspan=7, sticky=(W))

        self.load_birds_entry = ttk.Entry(self.daily_frame)
        self.load_birds_entry.grid(column=0, row=1, columnspan=4, sticky=(E, W))

        self.bird_file_button = ttk.Button(self.daily_frame)
        self.bird_file_button["text"] = "select files"
        self.bird_file_button["command"] =  self.set_bird_file

        self.bird_file_button.grid(column=6, row=1)

        self.load_birds_button = ttk.Button(self.daily_frame)
        self.load_birds_button["text"] = "load birds"
        self.load_birds_button["command"] =  self.load_birds

        self.load_birds_button.grid(column=7, row=1)
        
        self.sep1 = ttk.Separator(self.daily_frame)
        self.sep1.grid(column=0, row=2, columnspan=8, sticky=(N,S,E,W), ipadx=40)

        self.label3 = ttk.Label(self.daily_frame)
        self.label3["text"] = "generate daily risk for the following date(s): (in YYYY-MM-DD format)\n"
        self.label3.grid(column=0, row=3, columnspan=7, sticky=(W, S))

        self.label_entry1 = ttk.Label(self.daily_frame)
        self.label_entry1["text"] = "start date:"
        self.label_entry1.grid(column=0, row=4)

        self.daily_risk_entry1 = ttk.Entry(self.daily_frame)
        self.daily_risk_entry1.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.daily_risk_entry1.grid(column=1, row=4, sticky=(W, S))

        self.label_entry2 = ttk.Label(self.daily_frame)
        self.label_entry2["text"] = "end date:"
        self.label_entry2.grid(column=2, row=4)

        self.daily_risk_entry2 = ttk.Entry(self.daily_frame)
        self.daily_risk_entry2.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.daily_risk_entry2.grid(column=3, row=4, sticky=(W, S))

        self.daily_risk_button = ttk.Button(self.daily_frame)
        self.daily_risk_button["text"] = "run risk"
        self.daily_risk_button["command"] = self.run_daily_risk

        self.daily_risk_button.grid(column=7, row=4)

        self.daily_risk_params_frame = ttk.Frame(self.daily_frame)
            
        self.daily_risk_cs_label = ttk.Label(self.daily_risk_params_frame)
        self.daily_risk_cs_label["text"] = "closeness in space (miles):"
        self.daily_risk_cs_label.grid(column=0, row=50, sticky=(E))

        self.daily_risk_cs_entry = ttk.Entry(self.daily_risk_params_frame, width=5)
        self.daily_risk_cs_entry.insert(0, dycast.get_default_parameters()[0])
        self.daily_risk_cs_entry.grid(column=1, row=50)
        
        self.daily_risk_ct_label = ttk.Label(self.daily_risk_params_frame)
        self.daily_risk_ct_label["text"] = "closeness in time (days):"
        self.daily_risk_ct_label.grid(column=2, row=50, sticky=(E))
        
        self.daily_risk_ct_entry = ttk.Entry(self.daily_risk_params_frame, width=5)
        self.daily_risk_ct_entry.insert(0, dycast.get_default_parameters()[1])
        self.daily_risk_ct_entry.grid(column=3, row=50)
        
        self.daily_risk_sd_label = ttk.Label(self.daily_risk_params_frame)
        self.daily_risk_sd_label["text"] = "spatial domain (miles):"
        self.daily_risk_sd_label.grid(column=4, row=50, sticky=(E))

        self.daily_risk_sd_entry = ttk.Entry(self.daily_risk_params_frame, width=5)
        self.daily_risk_sd_entry.insert(0, dycast.get_default_parameters()[2])
        self.daily_risk_sd_entry.grid(column=5, row=50)
        
        self.daily_risk_td_label = ttk.Label(self.daily_risk_params_frame)
        self.daily_risk_td_label["text"] = "temporal domain (days):"
        self.daily_risk_td_label.grid(column=6, row=50, sticky=(E))
        
        self.daily_risk_td_entry = ttk.Entry(self.daily_risk_params_frame, width=5)
        self.daily_risk_td_entry.insert(0, dycast.get_default_parameters()[3])
        self.daily_risk_td_entry.grid(column=7, row=50) 
        
        self.daily_risk_params_frame.grid(column=0, row=50, columnspan=8)

        self.sep2 = ttk.Separator(self.daily_frame)
        self.sep2.grid(column=0, row=60, columnspan=8, sticky=(N,S,E,W), ipadx=40)

        self.label3 = ttk.Label(self.daily_frame)
        self.label3["text"] = "export daily risk for the following date(s): (in YYYY-MM-DD format)\n"
        self.label3.grid(column=0, row=70, columnspan=7, sticky=(W, S))

        self.label_export_dir_entry = ttk.Label(self.daily_frame)
        self.label_export_dir_entry["text"] = "export directory:"
        self.label_export_dir_entry.grid(column=0, row=80)

        self.export_dir_entry = ttk.Entry(self.daily_frame)
        self.export_dir_entry.grid(column=1, row=80, columnspan=6, sticky=(E,W))

        self.browse_export_dir_button = ttk.Button(self.daily_frame)
        self.browse_export_dir_button["text"] = "browse"
        self.browse_export_dir_button["command"] =  self.set_export_dir

        self.browse_export_dir_button.grid(column=7, row=80)

        self.label_entry1 = ttk.Label(self.daily_frame)
        self.label_entry1["text"] = "start date:"
        self.label_entry1.grid(column=0, row=90)

        self.export_risk_entry1 = ttk.Entry(self.daily_frame)
        self.export_risk_entry1.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.export_risk_entry1.grid(column=1, row=90, sticky=(W, S))

        self.label_entry2 = ttk.Label(self.daily_frame)
        self.label_entry2["text"] = "end date:"
        self.label_entry2.grid(column=2, row=90)

        self.export_risk_entry2 = ttk.Entry(self.daily_frame)
        self.export_risk_entry2.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.export_risk_entry2.grid(column=3, row=90, sticky=(W, S))

        self.export_risk_button = ttk.Button(self.daily_frame)
        self.export_risk_button["text"] = "export"
        self.export_risk_button["command"] = self.run_export_risk

        self.export_risk_button.grid(column=7, row=90)

        # Begin "postseason" page in the notebook

        self.postseason_frame.grid(column=0, row=0, columnspan=7, sticky=(E, W))
        
        self.label_kappa = ttk.Label(self.postseason_frame)
        self.label_kappa["text"] = "Kappa analysis:\n"
        self.label_kappa.grid(column=0, row=0)
        
        self.kappa_window_start_label = ttk.Label(self.postseason_frame)
        self.kappa_window_start_label["text"] = "window start:"
        self.kappa_window_start_label.grid(column=0, row=1, sticky=(E))

        self.kappa_window_start_entry = ttk.Entry(self.postseason_frame)
        self.kappa_window_start_entry.grid(column=1, row=1)
        
        self.kappa_window_end_label = ttk.Label(self.postseason_frame)
        self.kappa_window_end_label["text"] = "window end:"
        self.kappa_window_end_label.grid(column=2, row=1, sticky=(E))
        
        self.kappa_window_end_entry = ttk.Entry(self.postseason_frame)
        self.kappa_window_end_entry.grid(column=3, row=1)
        
        self.kappa_window_step_label = ttk.Label(self.postseason_frame)
        self.kappa_window_step_label["text"] = "window step:"
        self.kappa_window_step_label.grid(column=4, row=1, sticky=(E))
        
        self.kappa_window_step_entry = ttk.Entry(self.postseason_frame)
        self.kappa_window_step_entry.grid(column=5, row=1)
        
        self.kappa_lag_start_label = ttk.Label(self.postseason_frame)
        self.kappa_lag_start_label["text"] = "lag start:"
        self.kappa_lag_start_label.grid(column=0, row=2, sticky=(E))
        
        self.kappa_lag_start_entry = ttk.Entry(self.postseason_frame)
        self.kappa_lag_start_entry.grid(column=1, row=2)
        
        self.kappa_lag_end_label = ttk.Label(self.postseason_frame)
        self.kappa_lag_end_label["text"] = "lag end:"
        self.kappa_lag_end_label.grid(column=2, row=2, sticky=(E))
        
        self.kappa_lag_end_entry = ttk.Entry(self.postseason_frame)
        self.kappa_lag_end_entry.grid(column=3, row=2)
        
        self.kappa_lag_step_label = ttk.Label(self.postseason_frame)
        self.kappa_lag_step_label["text"] = "lag step:"
        self.kappa_lag_step_label.grid(column=4, row=2, sticky=(E)) 
        
        self.kappa_lag_step_entry = ttk.Entry(self.postseason_frame)
        self.kappa_lag_step_entry.grid(column=5, row=2)
        
        self.kappa_startdate_label = ttk.Label(self.postseason_frame)
        self.kappa_startdate_label["text"] = "start date:"
        self.kappa_startdate_label.grid(column=0, row=3, sticky=(E))

        self.kappa_startdate_entry = ttk.Entry(self.postseason_frame)
        self.kappa_startdate_entry.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.kappa_startdate_entry.grid(column=1, row=3)

        self.kappa_enddate_label = ttk.Label(self.postseason_frame)
        self.kappa_enddate_label["text"] = "end date:"
        self.kappa_enddate_label.grid(column=2, row=3, sticky=(E))

        self.kappa_enddate_entry = ttk.Entry(self.postseason_frame)
        self.kappa_enddate_entry.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.kappa_enddate_entry.grid(column=3, row=3)
       
        self.kappa_export_dir_label = ttk.Label(self.postseason_frame)
        self.kappa_export_dir_label["text"] = "export directory:"
        self.kappa_export_dir_label.grid(column=0, row=4, sticky=(E))
        
        self.kappa_export_dir_entry = ttk.Entry(self.postseason_frame)
        self.kappa_export_dir_entry.grid(column=1, row=4, columnspan=5, sticky=(E,W))
        
        self.kappa_export_dir_button = ttk.Button(self.postseason_frame)
        self.kappa_export_dir_button["text"] = "browse"
        self.kappa_export_dir_button["command"] = self.set_kappa_export_dir
        self.kappa_export_dir_button.grid(column=6, row=4)
        
        self.kappa_export_file_label = ttk.Label(self.postseason_frame)
        self.kappa_export_file_label["text"] = "export filename:"
        self.kappa_export_file_label.grid(column=0, row=5, sticky=(E))
        
        self.kappa_export_file_entry = ttk.Entry(self.postseason_frame)
        self.kappa_export_file_entry.insert(0, "kappa.tsv")
        self.kappa_export_file_entry.grid(column=1, row=5)
         
        self.kappa_button = ttk.Button(self.postseason_frame)
        self.kappa_button["text"] = "run kappa"
        self.kappa_button["command"] =  self.run_kappa
        
        self.kappa_button.grid(column=6, row=5)
       
        # Begin "initialization" page in the notebook
        
        self.init_frame.grid(column=0, row=0, columnspan=7, sticky=(E, W))
        
        self.init_frame.columnconfigure(1, weight=1)
        self.init_frame.columnconfigure(2, weight=2)
        self.init_frame.columnconfigure(3, weight=1)

        self.label_nmcm = ttk.Label(self.init_frame)
        self.label_nmcm["text"] = "Monte Carlo simulations:\n"
        self.label_nmcm.grid(column=0, row=0)
        
        self.nmcm_close_space_label = ttk.Label(self.init_frame)
        self.nmcm_close_space_label["text"] = "closeness in space (miles):"
        self.nmcm_close_space_label.grid(column=0, row=1, sticky=(E))

        self.nmcm_close_space_entry = ttk.Entry(self.init_frame, width=5)
        self.nmcm_close_space_entry.insert(0, dycast.get_default_parameters()[0])
        self.nmcm_close_space_entry.grid(column=1, row=1)
        
        self.nmcm_close_time_label = ttk.Label(self.init_frame)
        self.nmcm_close_time_label["text"] = "closeness in time (days):"
        self.nmcm_close_time_label.grid(column=2, row=1, sticky=(E))
        
        self.nmcm_close_time_entry = ttk.Entry(self.init_frame, width=5)
        self.nmcm_close_time_entry.insert(0, dycast.get_default_parameters()[1])
        self.nmcm_close_time_entry.grid(column=3, row=1)
        
        self.nmcm_spatial_domain_label = ttk.Label(self.init_frame)
        self.nmcm_spatial_domain_label["text"] = "spatial domain (miles):"
        self.nmcm_spatial_domain_label.grid(column=4, row=1, sticky=(E))

        self.nmcm_spatial_domain_entry = ttk.Entry(self.init_frame, width=5)
        self.nmcm_spatial_domain_entry.insert(0, dycast.get_default_parameters()[2])
        self.nmcm_spatial_domain_entry.grid(column=5, row=1)
        
        self.nmcm_temporal_domain_label = ttk.Label(self.init_frame)
        self.nmcm_temporal_domain_label["text"] = "temporal domain (days):"
        self.nmcm_temporal_domain_label.grid(column=6, row=1, sticky=(E))
        
        self.nmcm_temporal_domain_entry = ttk.Entry(self.init_frame, width=5)
        self.nmcm_temporal_domain_entry.insert(0, dycast.get_default_parameters()[3])
        self.nmcm_temporal_domain_entry.grid(column=7, row=1)
        
        self.nmcm_start_number_label = ttk.Label(self.init_frame)
        self.nmcm_start_number_label["text"] = "starting number of birds:"
        self.nmcm_start_number_label.grid(column=0, row=2, sticky=(E))

        self.nmcm_start_number_entry = ttk.Entry(self.init_frame, width=5)
        self.nmcm_start_number_entry.insert(0, dycast.get_default_threshold())
        self.nmcm_start_number_entry.grid(column=1, row=2)
        
        self.nmcm_end_number_label = ttk.Label(self.init_frame)
        self.nmcm_end_number_label["text"] = "ending number of birds:"
        self.nmcm_end_number_label.grid(column=2, row=2, sticky=(E))
        
        self.nmcm_end_number_entry = ttk.Entry(self.init_frame, width=5)
        self.nmcm_end_number_entry.insert(0, "100")
        self.nmcm_end_number_entry.grid(column=3, row=2)
        
        self.nmcm_button = ttk.Button(self.init_frame)
        self.nmcm_button["text"] = "run simulation"
        self.nmcm_button["command"] =  self.run_nmcm
        
        self.nmcm_button.grid(column=8, row=2)
      
        self.sep20 = ttk.Separator(self.init_frame)
        self.sep20.grid(column=0, row=5, columnspan=9, sticky=(N,S,E,W), ipadx=40)
        
        self.nmcm_load_label = ttk.Label(self.init_frame)
        self.nmcm_load_label["text"] = "Load precalculated Monte Carlo results:"
        self.nmcm_load_label.grid(column=0, row=6, columnspan=7, sticky=(W, S))
        
        self.nmcm_load_cs_label = ttk.Label(self.init_frame)
        self.nmcm_load_cs_label["text"] = "closeness in space (miles):"
        self.nmcm_load_cs_label.grid(column=0, row=7, sticky=(E))

        self.nmcm_load_cs_entry = ttk.Entry(self.init_frame, width=5)
        self.nmcm_load_cs_entry.insert(0, dycast.get_default_parameters()[0])
        self.nmcm_load_cs_entry.grid(column=1, row=7)
        
        self.nmcm_load_ct_label = ttk.Label(self.init_frame)
        self.nmcm_load_ct_label["text"] = "closeness in time (days):"
        self.nmcm_load_ct_label.grid(column=2, row=7, sticky=(E))
        
        self.nmcm_load_ct_entry = ttk.Entry(self.init_frame, width=5)
        self.nmcm_load_ct_entry.insert(0, dycast.get_default_parameters()[1])
        self.nmcm_load_ct_entry.grid(column=3, row=7)
        
        self.nmcm_load_sd_label = ttk.Label(self.init_frame)
        self.nmcm_load_sd_label["text"] = "spatial domain (miles):"
        self.nmcm_load_sd_label.grid(column=4, row=7, sticky=(E))

        self.nmcm_load_sd_entry = ttk.Entry(self.init_frame, width=5)
        self.nmcm_load_sd_entry.insert(0, dycast.get_default_parameters()[2])
        self.nmcm_load_sd_entry.grid(column=5, row=7)
        
        self.nmcm_load_td_label = ttk.Label(self.init_frame)
        self.nmcm_load_td_label["text"] = "temporal domain (days):"
        self.nmcm_load_td_label.grid(column=6, row=7, sticky=(E))
        
        self.nmcm_load_td_entry = ttk.Entry(self.init_frame, width=5)
        self.nmcm_load_td_entry.insert(0, dycast.get_default_parameters()[3])
        self.nmcm_load_td_entry.grid(column=7, row=7) 
        
        self.nmcm_load_file_label = ttk.Label(self.init_frame)
        self.nmcm_load_file_label["text"] = "filename:"
        self.nmcm_load_file_label.grid(column=0, row=90)
        
        self.nmcm_load_file_entry = ttk.Entry(self.init_frame)
        self.nmcm_load_file_entry.grid(column=1, row=90, columnspan=7, sticky=(E, W))
        
        self.nmcm_load_file_button = ttk.Button(self.init_frame)
        self.nmcm_load_file_button["text"] = "browse"
        self.nmcm_load_file_button["command"] = self.set_nmcm_import_file
        self.nmcm_load_file_button.grid(column=8, row=90)
        
        self.nmcm_load_button = ttk.Button(self.init_frame)
        self.nmcm_load_button["text"] = "load results"
        self.nmcm_load_button["command"] = self.load_nmcm
        self.nmcm_load_button.grid(column=8, row=100)
        
        ##
        
        self.n.add(self.daily_frame, text="Daily Tasks")
        self.n.add(self.postseason_frame, text="Post Season Tasks")
        self.n.add(self.init_frame, text="Initialization Tasks")

        self.status_label = ttk.Label(self, relief=SUNKEN, anchor=W)
        self.status_label["text"] = "Status: ready"
        self.status_label.grid(column=0, row=100, columnspan=7, sticky=(E, W))

    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)
        self.grid(column=0, row=0)
        self.connect_to_DYCAST()
        self.createWidgets()
        self.files = None
        self.export_dir = None

root = Tk()
root.title("DYCAST control")
app = DYCAST_control(master=root)
app.mainloop()
#root.destroy()
