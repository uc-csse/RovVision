# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# coding=utf-8
# =============================================================================
#  Copyright © 2017 FLIR Integrated Imaging Solutions, Inc. All Rights Reserved.
#
#  This software is the confidential and proprietary information of FLIR
#  Integrated Imaging Solutions, Inc. ("Confidential Information"). You
#  shall not disclose such Confidential Information and shall use it only in
#  accordance with the terms of the license agreement you entered into
#  with FLIR Integrated Imaging Solutions, Inc. (FLIR).
#
#  FLIR MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE SUITABILITY OF THE
#  SOFTWARE, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
#  PURPOSE, OR NON-INFRINGEMENT. FLIR SHALL NOT BE LIABLE FOR ANY DAMAGES
#  SUFFERED BY LICENSEE AS A RESULT OF USING, MODIFYING OR DISTRIBUTING
#  THIS SOFTWARE OR ITS DERIVATIVES.
# =============================================================================
#
#   ImageEvents.py shows how to acquire images using the image event handler.
#   It relies on information provided in the Enumeration, Acquisition,
#       and NodeMapInfo examples.
#
#       It can also be helpful to familiarize yourself with the NodeMapCallback
#       example, as nodemap callbacks follow the same general procedure as
#       events, but with a few less steps.
#
#       This example creates a user-defined class, ImageEventHandler, that inherits
#       from the Spinnaker class, ImageEvent. ImageEventHandler allows the user to
#       define any properties, parameters, and the event itself while ImageEvent
#       allows the child class to appropriately interface with Spinnaker.


import PySpin
from time import sleep
import numpy as np
import cv2

class TriggerType:
    SOFTWARE = 1
    HARDWARE = 2

CHOSEN_TRIGGER = TriggerType.HARDWARE

SLEEP_DURATION = 200  # amount of time for main thread to sleep for (in milliseconds) until _NUM_IMAGES have been saved


class ImageEventHandler(PySpin.ImageEvent):
    """
    This class defines the properties, parameters, and the event itself. Take a
    moment to notice what parts of the class are mandatory, and what have been
    added for demonstration purposes. First, any class used to define image events
    must inherit from ImageEvent. Second, the method signature of OnImageEvent()
    must also be consistent. Everything else - including the constructor,
    destructor, properties, body of OnImageEvent(), and other functions -
    is particular to the example.
    """
    _NUM_IMAGES = 10

    def __init__(self, cam):
        """
        Constructor. Retrieves serial number of given camera and sets image counter to 0.

        :param cam: Camera instance, used to get serial number for unique image filenames.
        :type cam: CameraPtr
        :rtype: None
        """
        super(ImageEventHandler, self).__init__()

        nodemap = cam.GetTLDeviceNodeMap()

        # Retrieve device serial number
        node_device_serial_number = PySpin.CStringPtr(nodemap.GetNode('DeviceSerialNumber'))

        if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
            self._device_serial_number = node_device_serial_number.GetValue()

        # Initialize image counter to 0
        self._image_count = 0

        # Release reference to camera
        # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being automatically
        # cleaned up when going out of scope.
        # The usage of del is preferred to assigning the variable to None.
        del cam

    def OnImageEvent(self, image):
        """
        This method defines an image event. In it, the image that triggered the
        event is converted and saved before incrementing the count. Please see
        Acquisition example for more in-depth comments on the acquisition
        of images.

        :param image: Image from event.
        :type image: ImagePtr
        :rtype: None
        """
        # Save max of _NUM_IMAGES Images
        if 1 or self._image_count < self._NUM_IMAGES:
            if self._image_count < self._NUM_IMAGES:
                print('Image event occurred...')

            # Check if image is incomplete
            if image.IsIncomplete():
                print('Image incomplete with image status %i...' % image.GetImageStatus())

            else:
                # Print image info
                if self._image_count < self._NUM_IMAGES:
                    print('Grabbed image %i, width = %i, height = %i' % (self._image_count,
                                                                     image.GetWidth(),
                                                                     image.GetHeight()))
                width = image.GetWidth()
                height = image.GetHeight()
                # Convert to mono8
                #image_converted = image.Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)
                image_converted = image.Convert(PySpin.PixelFormat_RGB8, PySpin.HQ_LINEAR)
                    #import ipdb;ipdb.set_trace() 
                self.theimage=image_converted.GetData().reshape((height,width,3))
                #cv2.imshow(self._device_serial_number,theimage)
                # Create unique filename and save image
                #if self._device_serial_number:
                #    filename = 'ImageEvents-%s-%i.jpg' % (self._device_serial_number, self._image_count)

                #else:  # if serial number is empty
                #    filename = 'ImageEvents-%i.jpg' % self._image_count

                #image_converted.Save(filename)

                #print('Image saved at %s\n' % filename)

                # Increment image counter
                self._image_count += 1

    def get_image_count(self):
        """
        Getter for image count.

        :return: Number of images saved.
        :rtype: int
        """
        return self._image_count

    def get_max_images(self):
        """
        Getter for maximum images.

        :return: Total number of images to save.
        :rtype: int
        """
        return self._NUM_IMAGES


def reset_image_events(cam, image_event_handler):
    """
    This functions resets the example by unregistering the image event.

    :param cam: Camera instance.
    :param image_event_handler: Image event handler for cam.
    :type cam: CameraPtr
    :type image_event_handler: ImageEventHandler
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    try:
        result = True

        #  Unregister image event handler
        #
        #  *** NOTES ***
        #  It is important to unregister all image events from all cameras they are registered to.
        #  Unlike SystemEventHandler and InterfaceEventHandler in the EnumerationEvents example,
        #  there is no need to explicitly delete the ImageEventHandler here as it does not store
        #  an instance of the camera (it gets deleted in the constructor already).
        cam.UnregisterEvent(image_event_handler)

        print('Image events unregistered...')

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        result = False

    return result


def print_device_info(nodemap):
    """
    This function prints the device information of the camera from the transport
    layer; please see NodeMapInfo example for more in-depth comments on printing
    device information from the nodemap.

    :param nodemap: Transport layer device nodemap from camera.
    :type nodemap: INodeMap
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    print('*** DEVICE INFORMATION ***')

    try:
        result = True
        node_device_information = PySpin.CCategoryPtr(nodemap.GetNode('DeviceInformation'))

        if PySpin.IsAvailable(node_device_information) and PySpin.IsReadable(node_device_information):
            features = node_device_information.GetFeatures()
            for feature in features:
                node_feature = PySpin.CValuePtr(feature)
                print('%s: %s' % (node_feature.GetName(),
                                  node_feature.ToString() if PySpin.IsReadable(node_feature) else 'Node not readable'))

        else:
            print('Device control information not available.')

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex.message)
        result = False

    return result

def configure_trigger(cam):
    """
    This function configures the camera to use a trigger. First, trigger mode is
    set to off in order to select the trigger source. Once the trigger source
    has been selected, trigger mode is then enabled, which has the camera
    capture only a single image upon the execution of the chosen trigger.

     :param cam: Camera to configure trigger for.
     :type cam: CameraPtr
     :return: True if successful, False otherwise.
     :rtype: bool
    """
    result = True

    print('*** CONFIGURING TRIGGER ***\n')

    if CHOSEN_TRIGGER == TriggerType.SOFTWARE:
        print('Software trigger chosen ...')
    elif CHOSEN_TRIGGER == TriggerType.HARDWARE:
        print('Hardware trigger chose ...')

    try:
        # Ensure trigger mode off
        # The trigger must be disabled in order to configure whether the source
        # is software or hardware.
        nodemap = cam.GetNodeMap()
        node_trigger_mode = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerMode'))
        if not PySpin.IsAvailable(node_trigger_mode) or not PySpin.IsReadable(node_trigger_mode):
            print('Unable to disable trigger mode (node retrieval). Aborting...')
            return False

        node_trigger_mode_off = node_trigger_mode.GetEntryByName('Off')
        if not PySpin.IsAvailable(node_trigger_mode_off) or not PySpin.IsReadable(node_trigger_mode_off):
            print('Unable to disable trigger mode (enum entry retrieval). Aborting...')
            return False

        node_trigger_mode.SetIntValue(node_trigger_mode_off.GetValue())

        print('Trigger mode disabled...')

        # Select trigger source
        # The trigger source must be set to hardware or software while trigger
        # mode is off.
        node_trigger_source = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerSource'))
        if not PySpin.IsAvailable(node_trigger_source) or not PySpin.IsWritable(node_trigger_source):
            print('Unable to get trigger source (node retrieval). Aborting...')
            return False

        if CHOSEN_TRIGGER == TriggerType.SOFTWARE:
            node_trigger_source_software = node_trigger_source.GetEntryByName('Software')
            if not PySpin.IsAvailable(node_trigger_source_software) or not PySpin.IsReadable(
                    node_trigger_source_software):
                print('Unable to set trigger source (enum entry retrieval). Aborting...')
                return False
            node_trigger_source.SetIntValue(node_trigger_source_software.GetValue())

        elif CHOSEN_TRIGGER == TriggerType.HARDWARE:
            node_trigger_source_hardware = node_trigger_source.GetEntryByName('Line2')
            if not PySpin.IsAvailable(node_trigger_source_hardware) or not PySpin.IsReadable(
                    node_trigger_source_hardware):
                print('Unable to set trigger source (enum entry retrieval). Aborting...')
                return False
            node_trigger_source.SetIntValue(node_trigger_source_hardware.GetValue())

        # Turn trigger mode on
        # Once the appropriate trigger source has been set, turn trigger mode
        # on in order to retrieve images using the trigger.
        node_trigger_mode_on = node_trigger_mode.GetEntryByName('On')
        if not PySpin.IsAvailable(node_trigger_mode_on) or not PySpin.IsReadable(node_trigger_mode_on):
            print('Unable to enable trigger mode (enum entry retrieval). Aborting...')
            return False

        node_trigger_mode.SetIntValue(node_trigger_mode_on.GetValue())
        print('Trigger mode turned back on...')

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False

    return result



def acquire_images(cam, nodemap, image_event_handler):
    """
    This function passively waits for images by calling wait_for_images(). Notice that
    this function is much shorter than the acquire_images() function of other examples.
    This is because most of the code has been moved to the image event's OnImageEvent()
    method.

    :param cam: Camera instance to grab images from.
    :param nodemap: Device nodemap.
    :param image_event_handler: Image event handler.
    :type cam: CameraPtr
    :type nodemap: INodeMap
    :type image_event_handler: ImageEventHandler
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    print('*** IMAGE ACQUISITION ***\n')
    try:
        result = True

        # Set acquisition mode to continuous
        node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
        if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
            print('Unable to set acquisition mode to continuous (enum retrieval). Aborting...')
            return False

        node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
        if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(node_acquisition_mode_continuous):
            print('Unable to set acquisition mode to continuous (entry retrieval). Aborting...')
            return False

        acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()
        node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

        print('Acquisition mode set to continuous...')

        # Begin acquiring images
        cam.BeginAcquisition()

        print('Acquiring images...')

        # Retrieve images using image event handler
        #wait_for_images(image_event_handler)

        #cam.EndAcquisition()

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        result = False

    return result


def run_single_camera(cams):
    """
    This function acts as the body of the example; please see NodeMapInfo example 
    for more in-depth comments on setting up cameras.

    :param cam: Camera to acquire images from.
    :type cam: CameraPtr
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    cams=list(cams)#[:1]
    try:
        result = True
        hdls=[]
        for i,cam in enumerate(cams):

                # Retrieve TL device nodemap and print device information
                nodemap_tldevice = cam.GetTLDeviceNodeMap()

                result &= print_device_info(nodemap_tldevice)

                # Initialize camera
                cam.Init()

                # Retrieve GenICam nodemap
                nodemap = cam.GetNodeMap()

                if configure_trigger(cam) is False:
                    return False

                # Configure image events
                #err, image_event_handler = configure_image_events(cam)
                image_event_handler = ImageEventHandler(cam)
                hdls.append(image_event_handler)
                cam.RegisterEvent(image_event_handler)

                node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
                if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
                    print('Unable to set acquisition mode to continuous (enum retrieval). Aborting...')
                    return False

                node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
                if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(node_acquisition_mode_continuous):
                    print('Unable to set acquisition mode to continuous (entry retrieval). Aborting...')
                    return False

                acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()
                node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

                print('Acquisition mode set to continuous...')
        for cam in cams:
                print('Acquisition start...')
                cam.BeginAcquisition()

        print('Acquisition start.2.')
                # Acquire images using the image event handler
                #result &= acquire_images(cam, nodemap, image_event_handler)
        cnt=0 
        while 1:
        #for i in range(1000*100): #10 sec
                for hdl in hdls:
                    if hdl._image_count>0:
                        cv2.imshow(hdl._device_serial_number,hdl.theimage[::2,::2,:])
                while cnt>hdl._image_count:
                    sleep(0.01)   
                cnt+=1
                k=cv2.waitKey(5) 
                if k==ord('q'):
                    break  
                if k!=-1:
                    print('k',k)
        for cam in cams:
            cam.EndAcquisition()
            # Reset image events
            result &= reset_image_events(cam, image_event_handler)

            # Deinitialize camera
            cam.DeInit()

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        result = False

    return result


def main():
    """
    Example entry point; please see Enumeration example for additional 
    comments on the steps in this function.

    :return: True if successful, False otherwise.
    :rtype: bool
    """
    result = True

    # Retrieve singleton reference to system object
    system = PySpin.System.GetInstance()

    # Retrieve list of cameras from the system
    cam_list = system.GetCameras()
    
    num_cams = cam_list.GetSize()

    print('Number of cameras detected: %i' % num_cams)

    # Finish if there are no cameras
    if num_cams == 0:
        # Clear camera list before releasing system
        cam_list.Clear()

        # Release system instance
        system.ReleaseInstance()

        print('Not enough cameras!')
        input('Done! Press Enter to exit...')

    # Run example on each camera
    #for i, cam in enumerate(cam_list):

    #    print('Running example for camera %d...' % i)

    result &= run_single_camera(cam_list)
    #    print('Camera %d example complete... \n' % i)

        # Release reference to camera
    #del cam
    for cam in cam_list:
        del cam
    # Clear camera list before releasing system
    cam_list.Clear()

    # Release system instance
    system.ReleaseInstance()
    #input('Done! Press Enter to exit...')

    return result

if __name__ == '__main__':
    main()
