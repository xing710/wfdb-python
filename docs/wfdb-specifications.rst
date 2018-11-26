WFDB Specifications
===================

-----------------------
Original Specifications
-----------------------

The wfdb-python package is built according to the specifications of the original WFDB package.

* `WFDB Software Package`_
* `WFDB Applications Guide`_
* `WFDB Header Specifications`_
* `WFDB Signal Specifications`_
* `WFDB Annotation Specifications`_

.. _WFDB Software Package: http://physionet.org/physiotools/wfdb.shtml
.. _WFDB Applications Guide: http://physionet.org/physiotools/wag/
.. _WFDB Header Specifications: https://physionet.org/physiotools/wag/header-5.htm
.. _WFDB Signal Specifications: https://physionet.org/physiotools/wag/signal-5.htm
.. _WFDB Annotation Specifications: https://physionet.org/physiotools/wag/annot-5.htm


-------------------------
Guide to WFDB Annotations
-------------------------

Annotation File
---------------

A WFDB annotation file contains:

* Information fields about the entire annotation set (optional) which include:

  - fs (optional): The sampling frequency of the record.
  - custom_labels: A mapping of the custom annotation labels defined in this file that are not part of the standard WFDB annotation labels (see annotation labels section).
* A set of annotations. Each individual annotation contains the following data fields:

  - sample: The annotation location in samples relative to the beginning of the record.
  - Label: *see annotation labels section.
  - subtype: The marked class/category of this annotation. Optional, default=0.
  - chan: The signal channel associated with this annotation. Optional, default=0.
  - num: A labelled number for the annotation, generally not used. Optional, default=0.
  - aux_note: The auxiliary note Optional, default=''.


For every annotation sample, the annotation file explictly stores
the 'sample' and 'symbol' fields, but not necessarily the others.



When reading annotation files, data fields which are
not stored in the file will either take their default values of 0, or
will be carried over from their previous values if any.



# The data fields for each individual annotation
ANN_DATA_FIELDS = ['sample', 'symbol', 'subtype', 'chan', 'num', 'aux_note',
    'label_store', 'description']

# Information fields describing the entire annotation set
ANN_INFO_FIELDS = ['record_name', 'extension', 'fs', 'custom_labels']

# Data fields describing the annotation label
ANN_LABEL_FIELDS = ('label_store', 'symbol', 'description')



chan : numpy array, optional
    A numpy array containing
num : numpy array, optional
    A numpy array containing


Annotation Data Fields
----------------------



Annotation Labels
-----------------

Aside from the sample location, the most important field of each annotation is its label that is used to categorize and visualize the annotation.

* label_store: The integer value actually stored in the annotation These values are what are actually stored in the annotation files themselves.
* symbol: The short symbol used to display the annotation. Up to
* description: The full descriptive text of the annotation.


When choosing labels for writing annotations, please follow these rules:
1. If your annotation indicates an event already contained in the standard wfdb annotation labels (call: `show_ann_labels`), please use that encoding. See example 1.
2. If you want to write a long comment note, use the `aux_note` field instead of the `symbol` field to store the comment. If you want the comment note is attached to a regular annotation, define the `aux_note` field of that annotation's index. See example 2a. Otherwise if the comment note comes by itself, set the label. See example 2b.

and use the 'comment annotation' label .

3. If you want to write a reoccuring event (such as a type of arrhthmic beat) that is not included in the standard wfdb annotation labels, define the `custom_labels` mapping of your annotation set. This is more efficient than adding the same aux_note to each recoccuring annotation. See example 3.



**Example 1 - Standard annotations**::

  wfdb.wrann(record='test', extension='ann', sample=np.array([100,200,300]),
             symbol=['N', 'N', 'N'])

**Example 2a - Adding auxiliary notes to regular annotations**::

  wfdb.wrann(record='test', extension='ann', sample=np.array([100,200,300,420]),
             symbol=['N', 'V', 'V', 'N'],
             aux_note=['', 'First ventricular beat', '', Sinus rhythm onwards'])

**Example 2b - Adding isolated auxiliary notes**::

  wfdb.wrann(record='test', extension='ann', sample=np.array([100,200,,300, 330]),
             symbol=['N', 'N', 'N', '"'],
             aux_note=['', '', '', 'Subject sneezes'])

**Example 3 - Including custom annotations**::

  custom_labels = pd.DataFrame(data=[(), ()], columns=['symbol', 'description'])



aux_note : list, optional
    A list containing the auxiliary information string (or None for
    annotations without notes) for each annotation.

fs : int, or float, optional
    The sampling frequency of the record.
label_store : numpy array, optional
    The integer value used to store/encode each annotation label
description : list, optional
    A list containing the descriptive string of each annotation label.
custom_labels : pandas dataframe, optional
    The custom annotation labels defined in the annotation file
    Maps the relationship between the three label fields. The
    DataFrame must have the three columns:
    ['label_store', 'symbol', 'description']



